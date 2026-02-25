import asyncio
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Protocol, Self

from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse

if TYPE_CHECKING:
    from types import TracebackType

class ISenderRunner(Protocol):
    """Protocol for an async queue-based message runner."""

    async def run(self, drain: bool = True) -> None:
        """Run the request processing loop until stopped.

        Args:
            drain: If ``True``, process all remaining requests
                in the queue after the stop signal is received.
        """
        ...

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        ...

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
        ...

    def results(self) -> AsyncGenerator[MessageResponse, None]:  # noqa: UP043
        """Yield responses as they become available.

        Terminates once the runner is stopped, the background
        task is done, and the response queue is empty.
        """
        ...

    async def result(self) -> MessageResponse:
        """Wait for and return the next available response.

        Raises:
            TimeoutError: If no response is available within
                1 second.
        """
        ...