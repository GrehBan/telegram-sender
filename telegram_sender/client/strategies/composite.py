import logging

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.protocols import ISendStrategy

logger = logging.getLogger(__name__)


class CompositeStrategy(ISendStrategy):
    """Runs multiple strategies as a sequential pipeline.

    The response produced by each strategy is forwarded to the
    next one, allowing strategies to build on or modify earlier
    results.

    Args:
        *strategies: Ordered sequence of strategies to execute.
    """

    def __init__(self, *strategies: ISendStrategy) -> None:
        self.strategies = strategies

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
        for strategy in self.strategies:
            logger.debug(
                "Executing strategy: '%s'",
                strategy.__class__.__name__,
            )
            response = await strategy(
                sender, runner, request, response
            )

        assert response is not None
        return response
