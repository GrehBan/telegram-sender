import logging

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.protocols import BaseSendStrategy

logger = logging.getLogger(__name__)


class PlainSendStrategy(BaseSendStrategy):
    """Basic strategy that simply dispatches the message via the sender.

    This strategy is **always** included at the end of the on-send
    pipeline by the ``SenderRunner`` to ensure the message is
    sent if no other strategy has produced a response.
    """

    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> MessageResponse:
        if response is not None:
            return response

        return await sender.send_message(request)
