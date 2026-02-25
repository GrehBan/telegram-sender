import logging
from typing import Generic, TypeVar, cast

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.protocols import (
    BasePostSendStrategy,
    BasePreSendStrategy,
    BaseSendStrategy,
)

logger = logging.getLogger(__name__)

StrategyT = TypeVar(
    "StrategyT",
    BasePreSendStrategy,
    BasePostSendStrategy,
    BaseSendStrategy
)


class BaseCompositeStrategy(Generic[StrategyT]):  # noqa: UP046
    """Base class for running multiple strategies as a sequential pipeline.
    """

    def add(self, strategy: StrategyT) -> None:
        """Add a strategy to the pipeline.

        Args:
            strategy: The strategy to add.
        """
        self.strategies.append(strategy)

    def __init__(
        self,
        *strategies: StrategyT
    ) -> None:
        """Initialize the composite strategy.

        Args:
            *strategies: Ordered sequence of strategies to execute.
        """
        self.strategies: list[StrategyT] = list(strategies)



class CompositePreSendStrategy(
    BaseCompositeStrategy[BasePreSendStrategy],
    BasePreSendStrategy
):
    """Sequential pipeline for pre-send strategies.
    """
    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> None:
        for strategy in self.strategies:
            await strategy.execute(
                sender,
                runner,
                request,
                response
            )


class CompositeSendStrategy(
    BaseCompositeStrategy[BaseSendStrategy],
    BaseSendStrategy
):
    """Sequential pipeline for on-send strategies.
    """
    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> MessageResponse:
        for strategy in self.strategies:
            response = await strategy.execute(
                sender,
                runner,
                request,
                response
            )
        return cast(MessageResponse, response)


class CompositePostSendStrategy(
    BaseCompositeStrategy[BasePostSendStrategy],
    BasePostSendStrategy
):
    """Sequential pipeline for post-send strategies.
    """
    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse,
    ) -> MessageResponse:
        for strategy in self.strategies:
            response = await strategy.execute(
                sender,
                runner,
                request,
                response
            )
        return response
