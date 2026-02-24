from typing import Protocol

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse


class ISendStrategy(Protocol):
    """Protocol for a send strategy in the processing pipeline.

    Strategies are called sequentially by ``CompositeStrategy``.
    Each strategy receives the response produced by the previous
    one. When ``response`` is ``None`` the strategy is the first
    in the chain and must send the message itself.
    """

    async def __call__(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> MessageResponse:
        """Execute the strategy.

        Args:
            sender: The message sender for dispatching.
            runner: The runner (used for re-queuing, etc.).
            request: The original message request.
            response: Response from a preceding strategy, or
                ``None`` if this is the first strategy.

        Returns:
            The (possibly modified) message response.
        """
        ...