Strategies API
==============

.. module:: telegram_sender.client.strategies

Pre-Send Strategies
-------------------

.. class:: telegram_sender.client.strategies.protocols.IPreSendStrategy

   ``typing.Protocol`` for a pre-send strategy in the processing pipeline.

   Executed *before* the message is sent.

   .. method:: __call__(sender, runner, request, response=None) -> None
      :async:
      :abstractmethod:

.. class:: telegram_sender.client.strategies.protocols.BasePreSendStrategy

   Base class for all pre-send strategies.

RateLimiterStrategy
^^^^^^^^^^^^^^^^^^^

.. class:: telegram_sender.client.strategies.rate_limit.RateLimiterStrategy(rate=20, period=60.0)

   Sliding-window rate limiter.

   Ensures no more than ``rate`` requests are sent within any rolling window
   of ``period`` seconds. When the limit is reached, the strategy sleeps
   until the oldest timestamp expires from the window.

   :param rate: Maximum number of requests per period.
   :type rate: int
   :param period: Sliding window length in seconds.
   :type period: float

On-Send Strategies
------------------

.. class:: telegram_sender.client.strategies.protocols.ISendStrategy

   ``typing.Protocol`` for an on-send strategy in the processing pipeline.

   Responsible for sending the message (if a response has not been produced
   by a previous strategy) or retrying.

   .. method:: __call__(sender, runner, request, response=None) -> MessageResponse
      :async:
      :abstractmethod:

.. class:: telegram_sender.client.strategies.protocols.BaseSendStrategy

   Base class for all on-send strategies.

PlainSendStrategy
^^^^^^^^^^^^^^^^^

.. class:: telegram_sender.client.strategies.send.PlainSendStrategy()

   Basic strategy that simply dispatches the message via the sender.

   This strategy is **always** included at the end of the on-send pipeline by
   ``SenderRunner`` as a final fallback. It ensures the message is sent if
   no other on-send strategy has produced a response.

TimeoutStrategy
^^^^^^^^^^^^^^^

.. class:: telegram_sender.client.strategies.timeout.TimeoutStrategy(timeout=5.0)

   Wraps the send call with ``asyncio.wait_for``.

   If a previous strategy already produced a response, it is returned
   immediately. The timeout only applies to the actual network call.

   :param timeout: Maximum wait time in seconds.
   :type timeout: float
   :raises TimeoutError: If the send does not complete within the timeout.

BaseRetryStrategy
^^^^^^^^^^^^^^^^^

.. class:: telegram_sender.client.strategies.retry.BaseRetryStrategy(attempts, delay)

   Abstract base class for retry strategies.

   Subclasses must implement ``_get_delay()`` to control wait times between
   retry attempts.

   :param attempts: Maximum number of retry attempts.
   :type attempts: int
   :param delay: Base delay in seconds.
   :type delay: float

   .. method:: _get_delay(attempt, error_value) -> float

      Calculate the delay before the next retry.

      :param attempt: Zero-based attempt index.
      :type attempt: int
      :param error_value: Numeric value from the error, or ``None``.
      :type error_value: int | float | None
      :returns: Delay in seconds.

   .. method:: execute(sender, runner, request, response=None) -> MessageResponse
      :async:

      If the initial response (either produced by this strategy or passed in)
      has an error, retry up to ``attempts`` times with the delay computed
      by ``_get_delay()``.

RetryStrategy
^^^^^^^^^^^^^

.. class:: telegram_sender.client.strategies.retry.RetryStrategy(attempts, delay)

   Retry strategy with a **fixed delay** between attempts.

   Uses ``error_value`` if available, otherwise falls back to ``delay``.

JitterStrategy
^^^^^^^^^^^^^^

.. class:: telegram_sender.client.strategies.jitter.JitterStrategy(attempts, delay, jitter_ratio=0.5)

   Retry strategy with **exponential backoff and random jitter**.

   Delay formula: ``base * 2^attempt + uniform(0, backoff * jitter_ratio)``.

   :param attempts: Maximum number of retry attempts.
   :type attempts: int
   :param delay: Base delay in seconds.
   :type delay: float
   :param jitter_ratio: Maximum jitter as a fraction of the backoff value.
   :type jitter_ratio: float

Post-Send Strategies
--------------------

.. class:: telegram_sender.client.strategies.protocols.IPostSendStrategy

   ``typing.Protocol`` for a post-send strategy in the processing pipeline.

   Executed *after* the message is sent. Receives and returns a
   ``MessageResponse``.

   .. method:: __call__(sender, runner, request, response) -> MessageResponse
      :async:
      :abstractmethod:

.. class:: telegram_sender.client.strategies.protocols.BasePostSendStrategy

   Base class for all post-send strategies.

DelayStrategy
^^^^^^^^^^^^^

.. class:: telegram_sender.client.strategies.delay.DelayStrategy(delay=1.0)

   Introduces a fixed delay after each send.

   If the response contains an ``RPCError`` whose ``value`` is a number
   (e.g. a Telegram flood-wait duration), that value is used as the delay
   instead of the configured default.

   :param delay: Default delay in seconds.
   :type delay: float

RequeueStrategy
^^^^^^^^^^^^^^^

.. class:: telegram_sender.client.strategies.requeue.RequeueStrategy(cycles=-1, per_request=False)

   Re-enqueues requests into the runner's queue after each send.

   Can track cycles either globally (shared) or per unique request object.

   :param cycles: Total number of re-enqueues allowed. ``-1`` means
       infinite.
   :type cycles: int
   :param per_request: If ``True``, track cycles for each request
       individually.
   :type per_request: bool

Composite Strategies
--------------------

.. class:: telegram_sender.client.strategies.composite.CompositePreSendStrategy(*strategies)

   Runs multiple pre-send strategies sequentially.

.. class:: telegram_sender.client.strategies.composite.CompositeSendStrategy(*strategies)

   Runs multiple on-send strategies sequentially.

.. class:: telegram_sender.client.strategies.composite.CompositePostSendStrategy(*strategies)

   Runs multiple post-send strategies sequentially.

Utilities
---------

.. function:: telegram_sender.client.strategies.utils.resolve_timeout(error, default=0.0)

   Safely extract a timeout value from an error.

   If the error is an ``RPCError`` with a numeric ``value`` attribute
   (e.g. flood-wait), that value is returned as a float. Otherwise,
   the default is returned.

   :param error: The exception to inspect.
   :type error: Exception | None
   :param default: Fallback value if no timeout is found.
   :type default: float
   :returns: Extracted timeout or default.
   :rtype: float
