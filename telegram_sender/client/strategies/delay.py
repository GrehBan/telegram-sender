import asyncio
import logging

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.protocols import ISendStrategy

logger = logging.getLogger(__name__)


class DelayStrategy(ISendStrategy):
    """Introduces a fixed delay after each send.

    If the response contains an error whose ``value`` is a
    number (e.g. a Telegram flood-wait duration), that value is
    used as the delay instead.

    Args:
        delay: Default delay in seconds between sends.
    """

    def __init__(
        self,
        delay: float = 1.0,
    ) -> None:
        self.delay = delay

    async def __call__(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> MessageResponse:
        return await self.execute(sender, runner, request, response)

    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> MessageResponse:
        if response is None:
            response = await sender.send_message(request)

        delay = response.error.value if (
            response.error and isinstance(response.error.value, (int, float))
        ) else self.delay

        logger.debug("Delaying next request by %.3fs", delay)
        await asyncio.sleep(delay)

        return response