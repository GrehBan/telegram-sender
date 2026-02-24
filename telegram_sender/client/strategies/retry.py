import asyncio
import logging

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.protocols import ISendStrategy

logger = logging.getLogger(__name__)


class BaseRetryStrategy(ISendStrategy):
    """Base class for retry strategies.

    Subclasses must implement ``_get_delay`` to control the
    wait time between retry attempts.

    Args:
        attempts: Maximum number of retry attempts.
        delay: Base delay in seconds between retries.
    """

    def __init__(self, attempts: int, delay: float) -> None:
        self.attempts = attempts
        self.delay = delay

    async def __call__(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> MessageResponse:
        return await self.execute(sender, runner, request, response)

    def _get_delay(
        self,
        attempt: int,
        error_value: int | float | None
    ) -> float:
        """Calculate the delay before the next retry.

        Args:
            attempt: Zero-based attempt index.
            error_value: Numeric value from the error (e.g.
                flood-wait seconds), or ``None``.

        Returns:
            Delay in seconds.
        """
        raise NotImplementedError

    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> MessageResponse:
        if response is None:
            response = await sender.send_message(request)

        if not response.error:
            return response

        for attempt in range(self.attempts):
            value = None
            if isinstance(response.error.value, (int, float)):
                value = response.error.value
            delay = self._get_delay(attempt, value)

            logger.debug(
                "Attempt %d/%d failed, retrying in %.3fs",
                attempt + 1,
                self.attempts,
                delay,
            )
            await asyncio.sleep(delay)

            response = await sender.send_message(request)
            if not response.error:
                return response

        return response


class RetryStrategy(BaseRetryStrategy):
    """Retry strategy with a fixed delay between attempts."""

    def _get_delay(
        self, attempt: int, error_value: float | None
    ) -> float:
        return error_value or self.delay
