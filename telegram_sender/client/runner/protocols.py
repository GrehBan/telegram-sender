import asyncio
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Protocol, Self

from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse

if TYPE_CHECKING:
    from types import TracebackType

class ISenderRunner(Protocol):
    """Protocol for an async queue-based message runner.

    Implementations accept requests, process them in a
    background task, and yield responses asynchronously.
    """

    async def run(self) -> None:
        """Start the processing loop."""

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
            A future that resolves to the response once
            the request has been handled.
        """
        ...

    def results(self) -> AsyncGenerator[MessageResponse, None]:  # noqa: UP043
        """Yield responses as they become available."""
        ...

    async def result(self) -> MessageResponse:
        """Wait for and return the next available response."""
        ...