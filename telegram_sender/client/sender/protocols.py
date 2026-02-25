from typing import TYPE_CHECKING, Protocol, Self

from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse

if TYPE_CHECKING:
    from types import TracebackType


class IMessageSender(Protocol):
    """Protocol for a Telegram message sender."""


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
        """Send a message described by *request*.

        Dispatches to the appropriate Telegram method based on
        the media type. All exceptions encountered during the send
        process (including Telegram ``RPCError``) are caught and wrapped into
        the returned ``MessageResponse`` instead of propagating.

        Args:
            request: The message request to send.

        Returns:
            A response containing either the sent message(s)
            or the captured error.
        """
        ...

    async def close(self) -> None:
        ...
