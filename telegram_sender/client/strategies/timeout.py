import asyncio
import logging

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.protocols import BaseSendStrategy

logger = logging.getLogger(__name__)


class TimeoutStrategy(BaseSendStrategy):
    """Wraps the send call with an ``asyncio.wait_for`` timeout.

    Must be placed **first** in a ``CompositeSendStrategy`` chain
    because ``TimeoutError`` propagates immediately, skipping
    any subsequent strategies.
    """

    def __init__(self, timeout: float = 5.0) -> None:
        """Initialize the timeout strategy.

        Args:
            timeout: Maximum time in seconds to wait for the send
                to complete.

        Raises:
            TimeoutError: If the send does not complete within
                the configured timeout.
        """
        self.timeout = timeout

    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> MessageResponse:
        if response is not None:
            return response

        try:
            return await asyncio.wait_for(
                sender.send_message(request),
                timeout=self.timeout,
            )
        except TimeoutError:
            logger.warning(
                "Request timed out after %ss: '%s'",
                self.timeout,
                request,
            )
            raise
