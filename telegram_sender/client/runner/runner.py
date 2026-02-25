import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Self

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.composite import (
    CompositePostSendStrategy,
    CompositePreSendStrategy,
    CompositeSendStrategy,
)
from telegram_sender.client.strategies.protocols import (
    BasePostSendStrategy,
    BasePreSendStrategy,
    BaseSendStrategy,
    BaseStrategy,
)
from telegram_sender.client.strategies.send import PlainSendStrategy
from telegram_sender.client.strategies.utils import resolve_timeout

if TYPE_CHECKING:
    from types import TracebackType

logger = logging.getLogger(__name__)


class SenderRunner(ISenderRunner):
    """Async queue-based runner that processes message requests.

    Wraps an ``IMessageSender`` and applies an optional chain of
    strategies organized into three phases (Pre-Send, On-Send, Post-Send)
    to every request. Runs a background ``asyncio`` task that
    sequentially pulls requests from a queue, executes them, and
    pushes responses to a separate results queue.

    Use as an async context manager::

        async with SenderRunner(sender, strategy) as runner:
            await runner.request(req)
            async for resp in runner.results():
                ...
    """

    def __init__(
        self,
        sender: IMessageSender,
        *strategies: BaseStrategy,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        """Initialize the sender runner.

        Args:
            sender: The sender used to dispatch messages.
            *strategies: Strategies applied to each request. They are
                automatically grouped into Pre-Send, On-Send, and
                Post-Send phases and executed in that order.
            loop: Optional event loop for creating futures. If not
                provided, the running loop is captured lazily.
        """
        self._requests: asyncio.Queue[
            tuple[MessageRequest, asyncio.Future[MessageResponse]]
        ] = asyncio.Queue()
        self._responses: asyncio.Queue[MessageResponse] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event = asyncio.Event()
        self.sender = sender
        self._loop = loop
        
        pre_send = []
        post_send = []
        on_send = []
        for strategy in strategies:
            if isinstance(strategy, BasePreSendStrategy):
                pre_send.append(strategy)
            elif isinstance(strategy, BasePostSendStrategy):
                post_send.append(strategy)
            elif isinstance(strategy, BaseSendStrategy):
                on_send.append(strategy)

        self.pre_send = CompositePreSendStrategy(*pre_send)
        self.post_send = CompositePostSendStrategy(*post_send)
        on_send.append(PlainSendStrategy())
        self.on_send = CompositeSendStrategy(*on_send)

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Return the event loop the runner is bound to.

        The loop is captured lazily on first access if not
        explicitly provided during initialization.

        Raises:
            RuntimeError: If no loop is running or there is a
                loop mismatch.
        """
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            if self._loop:
                return self._loop
            raise RuntimeError(
                "No running event loop detected. "
                "Ensure the runner is used within an async context."
            ) from None

        if self._loop and running is not self._loop:
            raise RuntimeError(
                f"Loop mismatch: runner is bound to {self._loop}, "
                f"but is being used in {running}. "
                "Ensure the runner is used within the loop it was created in."
            )

        if self._loop is None:
            self._loop = running

        return running

    @property
    def task(self) -> asyncio.Task[None]:
        """Return the background processing task.

        Raises:
            RuntimeError: If the runner has not been started
                via the async context manager.
        """
        if self._task is None:
            raise RuntimeError(
                "Task is not initialized. "
                f"Use 'async with {self.__class__.__name__}()'"
            )
        return self._task

    async def __aenter__(self) -> Self:
        await self.sender.__aenter__()
        self._task = asyncio.create_task(self.run())
        logger.info("Runner started")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()
        await self.sender.__aexit__(exc_type, exc_val, exc_tb)

    async def request(
        self,
        request: MessageRequest
    ) -> asyncio.Future[MessageResponse]:
        if self._stop_event.is_set():
            # for correct draining
            logger.warning(
                "Runner is stopped, dropping request"
            )
            return asyncio.Future()

        future: asyncio.Future[MessageResponse] = self.loop.create_future()
        await self._requests.put((request, future))
        logger.debug(
            "Request enqueued for chat_id=%s (queue_size=%d)",
            request.chat_id,
            self._requests.qsize(),
        )
        return future

    async def close(self) -> None:
        """Signal the runner to stop and drain remaining requests."""
        logger.info("Runner stopping, draining remaining requests...")
        self._stop_event.set()
        await self.task
        logger.info("Runner stopped")

    async def result(self) -> MessageResponse:
        return await asyncio.wait_for(self._responses.get(), timeout=1.0)

    async def results(self) -> AsyncGenerator[MessageResponse, None]:  # noqa: UP043
        while True:
            try:
                yield await self.result()
            except TimeoutError:
                if not self._stop_event.is_set():
                    continue
                if not self.task.done():
                    continue
                if self._responses.empty():
                    break

    async def _handle_request(
        self,
        request: MessageRequest,
        future: asyncio.Future[MessageResponse]
    ) -> None:
        try:
            if self.pre_send:
                await self.pre_send.execute(
                    self.sender,
                    self,
                    request,
                )
            
            response = await self.on_send.execute(
                self.sender,
                self,
                request,
            )
            if self.post_send:
                response = await self.post_send.execute(
                    self.sender,
                    self,
                    request,
                    response,
                )
        except Exception as err:
            logger.error(
                "Exception handling request for chat_id=%s: %s",
                request.chat_id,
                err,
            )
            response = MessageResponse(
                original=None,
                error=err,
            )
        finally:
            self._requests.task_done()

        await self._responses.put(response)

        if error := response.error:
            logger.warning(
                "Request for chat_id=%s resulted in error: %s",
                request.chat_id,
                error,
            )
            if not future.done():
                future.set_exception(error)
            
            if wait_time := resolve_timeout(error):
                logger.warning(
                    "Sleeping %ss after error for chat_id=%s",
                    wait_time,
                    request.chat_id,
                )
                await asyncio.sleep(wait_time)
        elif not future.done():
            future.set_result(response)

    async def _drain(self) -> None:
        while not self._requests.empty():
            request, future = self._requests.get_nowait()
            await self._handle_request(request, future)

    async def run(self, drain: bool = True) -> None:
        self._stop_event.clear()

        while not self._stop_event.is_set():
            try:
                request, future = await asyncio.wait_for(
                    self._requests.get(), timeout=1.0
                )
            except TimeoutError:
                continue

            await self._handle_request(request, future)

        if drain:
            await self._drain()