import asyncio
import logging
import time
from collections import deque

from telegram_sender.client.runner.protocols import ISenderRunner
from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.client.strategies.protocols import BasePreSendStrategy

logger = logging.getLogger(__name__)


class RateLimiterStrategy(BasePreSendStrategy):
    """Sliding-window rate limiter.

    Ensures no more than ``rate`` requests are sent within any
    rolling window of ``period`` seconds.
    """

    def __init__(
        self,
        rate: int = 20,
        period: float = 60.0,
    ) -> None:
        """Initialize the rate limiter strategy.

        Args:
            rate: Maximum number of requests allowed per period.
            period: Length of the sliding window in seconds.
        """
        self.rate = rate
        self.period = period
        self._timestamps: deque[float] = deque()

    def _cleanup(self, now: float) -> None:
        while self._timestamps and now - self._timestamps[0] >= self.period:
            self._timestamps.popleft()

    async def _wait(self) -> None:
        while True:
            now = time.monotonic()
            self._cleanup(now)

            if len(self._timestamps) < self.rate:
                self._timestamps.append(now)
                return

            wait_for = self.period - (now - self._timestamps[0])
            logger.debug(
                "Rate limit reached (%d/%.1fs), waiting %.3fs",
                self.rate,
                self.period,
                wait_for,
            )
            await asyncio.sleep(wait_for)

    async def execute(
        self,
        sender: IMessageSender,
        runner: ISenderRunner,
        request: MessageRequest,
        response: MessageResponse | None = None,
    ) -> None:
        await self._wait()