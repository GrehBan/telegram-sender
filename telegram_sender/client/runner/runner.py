import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Self

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.composite import CompositeStrategy
from telegram_sender.client.strategies.protocols import ISendStrategy

if TYPE_CHECKING:
    from types import TracebackType

logger = logging.getLogger(__name__)


class SenderRunner(ISenderRunner):
    """Async queue-based runner that processes message requests.

    Wraps an ``IMessageSender`` and applies an optional chain of
    strategies to every request. Runs a background ``asyncio``
    task that pulls requests from a queue, executes them, and
    pushes responses to a separate results queue.

    Use as an async context manager::

        async with SenderRunner(sender, strategy) as runner:
            await runner.request(req)
            async for resp in runner.results():
                ...

    Args:
        sender: The sender used to dispatch messages.
        *strategies: Strategies applied to each request in
            order via ``CompositeStrategy``.
        loop: Event loop for creating futures. Defaults to the
            running loop.
    """

    def __init__(
        self,
        sender: IMessageSender,
        *strategies: ISendStrategy,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self._requests: asyncio.Queue[
            tuple[MessageRequest, asyncio.Future[MessageResponse]]
        ] = asyncio.Queue()
        self._responses: asyncio.Queue[MessageResponse] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event = asyncio.Event()
        self.sender = sender
        self._loop = loop or asyncio.get_running_loop()
        self._strategy = CompositeStrategy(*strategies) if strategies else None

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
        """Enqueue a message request for processing.

        Args:
            request: The message request to enqueue.

        Returns:
            A future resolved when the request is handled.
        """
        future: asyncio.Future[MessageResponse] = self._loop.create_future()
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
        """Wait for and return the next available response.

        Raises:
            TimeoutError: If no response is available within
                1 second.
        """
        return await asyncio.wait_for(self._responses.get(), timeout=1.0)

    async def results(self) -> AsyncGenerator[MessageResponse, None]:  # noqa: UP043
        """Yield responses as they become available.

        Terminates once the runner is stopped, the background
        task is done, and the response queue is empty.
        """
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
            if self._strategy:
                response = await self._strategy(
                    self.sender, self, request
                )
            else:
                response = await self.sender.send_message(request=request)
        except Exception as err:
            logger.error(
                "Exception handling request for chat_id=%s: %s",
                request.chat_id,
                err,
            )
            if not future.done():
                future.set_exception(err)
            return
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
            if isinstance((value := error.value), (int, float)):
                logger.debug(
                    "Sleeping %ss after error for chat_id=%s",
                    value,
                    request.chat_id,
                )
                await asyncio.sleep(value)
        elif not future.done():
            future.set_result(response)

    async def _drain(self) -> None:
        while not self._requests.empty():
            request, future = self._requests.get_nowait()
            await self._handle_request(request, future)

    async def run(self) -> None:
        """Run the request processing loop until stopped."""
        self._stop_event.clear()

        while not self._stop_event.is_set():
            try:
                request, future = await asyncio.wait_for(
                    self._requests.get(), timeout=1.0
                )
            except TimeoutError:
                continue

            await self._handle_request(request, future)

        await self._drain()