import asyncio
import logging

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.protocols import BasePostSendStrategy
from telegram_sender.client.strategies.utils import resolve_timeout

logger = logging.getLogger(__name__)


class DelayStrategy(BasePostSendStrategy):
    """Introduces a fixed delay after each send.

    If the response contains an error whose ``value`` is a
    number (e.g. a Telegram flood-wait duration), that value is
    used as the delay instead.
    """

    def __init__(
        self,
        delay: float = 1.0,
    ) -> None:
        """Initialize the delay strategy.

        Args:
            delay: Default delay in seconds between sends.
        """
        self.delay = delay

    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse,
    ) -> MessageResponse:
        delay = resolve_timeout(response.error, default=self.delay)

        logger.debug("Delaying next request by %.3fs", delay)
        await asyncio.sleep(delay)

        return response