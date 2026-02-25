"""Composable message sending strategies."""

from telegram_sender.client.strategies.delay import DelayStrategy
from telegram_sender.client.strategies.jitter import JitterStrategy
from telegram_sender.client.strategies.rate_limit import RateLimiterStrategy
from telegram_sender.client.strategies.requeue import RequeueStrategy
from telegram_sender.client.strategies.retry import RetryStrategy
from telegram_sender.client.strategies.send import PlainSendStrategy
from telegram_sender.client.strategies.timeout import TimeoutStrategy
from telegram_sender.client.strategies.utils import resolve_timeout

__all__ = [
    "DelayStrategy",
    "JitterStrategy",
    "PlainSendStrategy",
    "RateLimiterStrategy",
    "RequeueStrategy",
    "RetryStrategy",
    "TimeoutStrategy",
    "resolve_timeout",
]
