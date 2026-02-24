import logging

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.protocols import ISendStrategy

logger = logging.getLogger(__name__)


class RequeueStrategy(ISendStrategy):
    """Re-enqueues the request into the runner after each send.

    Useful for sending the same message repeatedly. The request
    is placed back into the runner's queue without awaiting the
    result.

    The counter is **global** across all requests handled by
    this strategy instance. Once the limit is reached, no
    further requests will be re-enqueued.

    Args:
        cycles: Total number of re-enqueues allowed across
            all requests. ``-1`` means infinite.
    """

    def __init__(self, cycles: int = -1) -> None:
        self.cycles = cycles
        self._count: int = 0

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

        if self.cycles == -1 or self._count < self.cycles:
            self._count += 1
            logger.debug("Requeuing request, cycle: %d", self._count)
            await runner.request(request)

        return response