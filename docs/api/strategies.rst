Strategies API
==============

.. module:: telegram_sender.client.strategies

ISendStrategy
-------------

.. class:: telegram_sender.client.strategies.protocols.ISendStrategy

   ``typing.Protocol`` for a send strategy in the processing pipeline.

   Strategies are called sequentially by ``CompositeStrategy``.  Each
   receives the response produced by the previous one.  When ``response``
   is ``None`` the strategy is the first in the chain and must send the
   message itself.

   .. method:: __call__(sender, runner, request, response=None) -> MessageResponse
      :async:
      :abstractmethod:

      :param sender: The message sender for dispatching.
      :type sender: IMessageSender
      :param runner: The runner (used for re-queuing, etc.).
      :type runner: ISenderRunner
      :param request: The original message request.
      :type request: MessageRequest
      :param response: Response from a preceding strategy, or ``None`` if
          this is the first strategy.
      :type response: MessageResponse | None
      :returns: The (possibly modified) message response.

CompositeStrategy
-----------------

.. class:: telegram_sender.client.strategies.composite.CompositeStrategy(*strategies)

   Runs multiple strategies as a sequential pipeline.

   The response produced by each strategy is forwarded to the next one.

   :param \*strategies: Ordered sequence of strategies to execute.
   :type \*strategies: ISendStrategy

   .. method:: execute(sender, runner, request, response=None) -> MessageResponse
      :async:

      Execute all strategies in order, piping the response through.

DelayStrategy
-------------

.. class:: telegram_sender.client.strategies.delay.DelayStrategy(delay=1.0)

   Introduces a fixed delay after each send.

   If the response contains an ``RPCError`` whose ``value`` is a number
   (e.g. a Telegram flood-wait duration), that value is used as the delay
   instead of the configured default.

   :param delay: Default delay in seconds.
   :type delay: float

   .. method:: execute(sender, runner, request, response=None) -> MessageResponse
      :async:

RequeueStrategy
---------------

.. class:: telegram_sender.client.strategies.requeue.RequeueStrategy(cycles=-1)

   Re-enqueues the request into the runner's queue after each send.

   The request is placed back into the queue via ``runner.request()``
   **without** awaiting the returned future (fire-and-forget).

   The counter is **global** across all requests handled by this strategy
   instance.  Once the limit is reached, no further requests will be
   re-enqueued.

   :param cycles: Total number of re-enqueues allowed.  ``-1`` means
       infinite.
   :type cycles: int

   .. method:: execute(sender, runner, request, response=None) -> MessageResponse
      :async:

BaseRetryStrategy
-----------------

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

      If the initial response (or first send) has an error, retry up to
      ``attempts`` times with the delay computed by ``_get_delay()``.

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

RateLimiterStrategy
-------------------

.. class:: telegram_sender.client.strategies.rate_limit.RateLimiterStrategy(rate=20, period=60.0)

   Sliding-window rate limiter.

   Ensures no more than ``rate`` requests are sent within any rolling window
   of ``period`` seconds.  When the limit is reached, the strategy sleeps
   until the oldest timestamp expires from the window.

   :param rate: Maximum number of requests per period.
   :type rate: int
   :param period: Sliding window length in seconds.
   :type period: float

   .. method:: execute(sender, runner, request, response=None) -> MessageResponse
      :async:

TimeoutStrategy
---------------

.. class:: telegram_sender.client.strategies.timeout.TimeoutStrategy(timeout=5.0)

   Wraps the send call with ``asyncio.wait_for``.

   If a previous strategy already produced a response, it is returned
   immediately.  The timeout only applies to the actual network call.

   .. warning::

      Must be placed **first** in a ``CompositeStrategy`` chain because
      ``TimeoutError`` propagates immediately, skipping any subsequent
      strategies.

   :param timeout: Maximum wait time in seconds.
   :type timeout: float
   :raises TimeoutError: If the send does not complete within the timeout.

   .. method:: execute(sender, runner, request, response=None) -> MessageResponse
      :async:
