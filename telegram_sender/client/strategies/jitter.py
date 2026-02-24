import logging
import random

from telegram_sender.client.strategies.retry import BaseRetryStrategy

logger = logging.getLogger(__name__)


class JitterStrategy(BaseRetryStrategy):
    """Retry strategy with exponential backoff and random jitter.

    On each attempt the delay is ``base * 2^attempt`` plus a
    uniformly random jitter up to ``jitter_ratio`` of the
    backoff value.

    Args:
        attempts: Maximum number of retry attempts.
        delay: Base delay in seconds for backoff calculation.
        jitter_ratio: Maximum jitter as a fraction of the
            exponential backoff value.
    """

    def __init__(
        self,
        attempts: int,
        delay: float,
        jitter_ratio: float = 0.5,
    ) -> None:
        super().__init__(attempts, delay)
        self.jitter_ratio = jitter_ratio

    def _get_delay(
        self, attempt: int, error_value: float | None
    ) -> float:
        exp_backoff: float = (error_value or self.delay) * (
            2 ** attempt
        )
        jitter: float = random.uniform(
            0, exp_backoff * self.jitter_ratio
        )
        total: float = exp_backoff + jitter
        logger.debug(
            "Jitter delay: backoff=%.3fs, jitter=%.3fs, "
            "total=%.3fs (attempt %d)",
            exp_backoff,
            jitter,
            total,
            attempt + 1,
        )
        return total