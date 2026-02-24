from typing import TYPE_CHECKING, Protocol, Self

from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse

if TYPE_CHECKING:
    from types import TracebackType


class IMessageSender(Protocol):
    """Protocol for a Telegram message sender.

    Implementations must be usable as async context managers
    and expose ``send_message`` for dispatching requests.
    """

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        ...

    async def send_message(
        self,
        request: MessageRequest
    ) -> MessageResponse:
        """Send a single message described by *request*.

        Args:
            request: The message request to send.

        Returns:
            A response containing either the sent message or
            an error.
        """
        ...

    async def close(self) -> None:
        """Release underlying resources."""
        ...
