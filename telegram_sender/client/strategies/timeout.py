import asyncio
import logging

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.protocols import ISendStrategy

logger = logging.getLogger(__name__)


class TimeoutStrategy(ISendStrategy):
    """Wraps the send call with an ``asyncio.wait_for`` timeout.

    If a previous strategy already produced a response, it is
    returned immediately (the timeout only applies to the actual
    network call).

    Must be placed **first** in a ``CompositeStrategy`` chain
    because ``TimeoutError`` propagates immediately, skipping
    any subsequent strategies.

    Args:
        timeout: Maximum time in seconds to wait for the send
            to complete.

    Raises:
        TimeoutError: If the send does not complete within
            the configured timeout.
    """

    def __init__(self, timeout: float = 5.0) -> None:
        self.timeout = timeout

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