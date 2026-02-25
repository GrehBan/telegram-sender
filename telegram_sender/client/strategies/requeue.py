import logging
from collections import defaultdict

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.protocols import BasePostSendStrategy

logger = logging.getLogger(__name__)


class RequeueStrategy(BasePostSendStrategy):
    """Re-enqueues requests into the runner after each send.

    The strategy can track cycles either globally (shared across
    all requests) or per unique request object.
    """

    def __init__(self, cycles: int = -1, per_request: bool = False) -> None:
        """Initialize the requeue strategy.

        Args:
            cycles: Total number of re-enqueues allowed.
                ``-1`` means infinite.
            per_request: If ``True``, the ``cycles`` limit is
                applied to each unique request individually.
                If ``False``, the limit is global.
        """
        self.cycles = cycles
        self.per_request = per_request
        self._global_count: int = 0
        self._request_counts: dict[MessageRequest, int] = defaultdict(int)

    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse,
    ) -> MessageResponse:
        count = (
            self._request_counts[request]
            if self.per_request
            else self._global_count
        )

        if self.cycles == -1 or count < self.cycles:
            if self.per_request:
                self._request_counts[request] += 1
                label = f"Request (for {request.chat_id})"
            else:
                self._global_count += 1
                label = "Global"

            logger.debug(
                "%s requeue: %d/%s",
                label,
                count + 1,
                self.cycles if self.cycles != -1 else "inf",
            )
            await runner.request(request)

        return response
