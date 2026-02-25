from typing import Protocol, TypeAlias

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse


class IPreSendStrategy(Protocol):
    """Protocol for strategies executed before sending a message.

    Pre-send strategies perform actions like logging, validation, or
    preparation. They do not produce a response.
    """
    async def __call__(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> None:
        """Execute the strategy.

        Args:
            sender: The message sender for dispatching.
            runner: The runner (used for re-queuing, etc.).
            request: The original message request.
            response: ``None``

        Returns:
            None
        """
        ...

    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> None:
        """Execute the strategy.

        Args:
            sender: The message sender for dispatching.
            runner: The runner (used for re-queuing, etc.).
            request: The original message request.
            response: None

        Returns:
            None
        """
        ...


class ISendStrategy(Protocol):
    """Protocol for strategies responsible for sending a message.

    On-send strategies are responsible for producing a ``MessageResponse``.
    They can implement custom sending logic or retry mechanisms.
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
            response: Response from a preceding strategy, or ``None``.

        Returns:
            The (possibly modified) message response.
        """
        ...

    async def execute(
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
            response: Response from a preceding strategy, or None.

        Returns:
            MessageResponse
        """
        ...


class IPostSendStrategy(Protocol):
    """Protocol for strategies executed after sending a message.

    Post-send strategies receive the ``MessageResponse`` and can
    perform actions like delaying the next request or re-queuing.
    """
    async def __call__(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse,
    ) -> MessageResponse:
        """Execute the strategy.

        Args:
            sender: The message sender for dispatching.
            runner: The runner (used for re-queuing, etc.).
            request: The original message request.
            response: message response

        Returns:
            The (possibly modified) message response.
        """
        ...

    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse,
    ) -> MessageResponse:
        """Execute the strategy.

        Args:
            sender: The message sender for dispatching.
            runner: The runner (used for re-queuing, etc.).
            request: The original message request.
            response: message response

        Returns:
            The (possibly modified) message response.
        """
        ...


class BasePostSendStrategy(IPostSendStrategy):
    """Base class for post send strategies.
    """
    async def __call__(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse,
    ) -> MessageResponse:
        return await self.execute(sender, runner, request, response)

    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse,
    ) -> MessageResponse:
        raise NotImplementedError


class BasePreSendStrategy(IPreSendStrategy):
    """Base class for pre send strategies.
    """
    async def __call__(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> None:
        return await self.execute(sender, runner, request, response)

    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> None:
        raise NotImplementedError


class BaseSendStrategy(ISendStrategy):
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
        raise NotImplementedError

BaseStrategy: TypeAlias = (  # noqa: UP040
    BasePreSendStrategy | 
    BaseSendStrategy | 
    BasePostSendStrategy
)
