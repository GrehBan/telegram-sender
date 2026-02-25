Strategies Guide
================

Strategies are composable behaviours applied to every message request. They are
organized into three distinct execution phases in the pipeline:

1.  **Pre-Send**: Executed before the message is sent (no response available).
2.  **On-Send**: Responsible for actually sending the message (returns a response).
3.  **Post-Send**: Executed after the message is sent (receives and returns a response).

The ``SenderRunner`` automatically categorizes strategies based on their type.

Built-in strategies
-------------------

Pre-Send Strategies
^^^^^^^^^^^^^^^^^^^

RateLimiterStrategy
~~~~~~~~~~~~~~~~~~~

Sliding-window rate limiter that ensures no more than ``rate`` requests are
sent within any rolling ``period``.

.. code-block:: python

   from telegram_sender.client.strategies.rate_limit import RateLimiterStrategy

   RateLimiterStrategy(rate=20, period=60.0)  # 20 req / 60 s

When the limit is reached the strategy sleeps until the oldest timestamp
expires from the window.

On-Send Strategies
^^^^^^^^^^^^^^^^^^

PlainSendStrategy
~~~~~~~~~~~~~~~~~

The basic strategy that simply dispatches the message via the sender. This
strategy is **always** appended to the On-Send pipeline by the
``SenderRunner`` as a final fallback. It only sends the message if no
preceding strategy (like ``TimeoutStrategy``) has already produced a response.

TimeoutStrategy
~~~~~~~~~~~~~~~

Wraps the message send call with ``asyncio.wait_for``.

.. code-block:: python

   from telegram_sender.client.strategies.timeout import TimeoutStrategy

   TimeoutStrategy(timeout=10.0)

RetryStrategy
~~~~~~~~~~~~~

Retries the send on error with a fixed delay between attempts.

.. code-block:: python

   from telegram_sender.client.strategies.retry import RetryStrategy

   RetryStrategy(attempts=3, delay=2.0)

If the error carries a numeric ``value`` (e.g. flood-wait seconds), it is
used instead of the fixed ``delay``.

JitterStrategy
~~~~~~~~~~~~~~

Retries with exponential backoff plus random jitter:

.. math::

   \text{delay} = \text{base} \times 2^{\text{attempt}} + \text{uniform}(0,\; \text{backoff} \times \text{jitter\_ratio})

.. code-block:: python

   from telegram_sender.client.strategies.jitter import JitterStrategy

   JitterStrategy(attempts=5, delay=1.0, jitter_ratio=0.5)

.. note::

   If multiple ``On-Send`` strategies are provided, the first one in the chain is
   responsible for sending the message. Subsequent ones will receive the
   response and can decide whether to send again (like ``RetryStrategy`` does
   on error) or return it immediately.

Post-Send Strategies
^^^^^^^^^^^^^^^^^^^^

DelayStrategy
~~~~~~~~~~~~~

Introduces a fixed pause after each send.

.. code-block:: python

   from telegram_sender.client.strategies.delay import DelayStrategy

   DelayStrategy(delay=5.0)   # 5-second delay

If the response contains an ``RPCError`` whose ``value`` is numeric (e.g. a
flood-wait duration), that value overrides the configured delay.

RequeueStrategy
~~~~~~~~~~~~~~~

Re-enqueues requests into the runner's queue after each send.

.. code-block:: python

   from telegram_sender.client.strategies.requeue import RequeueStrategy

   # Global: stop after 10 total messages sent across all requests
   RequeueStrategy(cycles=10, per_request=False)

   # Per-Request: each unique message is sent up to 6 times
   RequeueStrategy(cycles=5, per_request=True)

.. note::

   When ``per_request=True``, the strategy uses the ``MessageRequest`` object
   itself as a key to track counts. Ensure you pass the same object instance to
   ``runner.request()`` to trigger the per-request limit.

Composing strategies
--------------------

Pass multiple strategies to ``SenderRunner``. They are automatically grouped
and executed in their respective phases:

.. code-block:: python

   runner = SenderRunner(
       sender,
       TimeoutStrategy(timeout=5),   # On-Send
       RetryStrategy(attempts=3),     # On-Send (retries the timeout send)
       DelayStrategy(delay=10),      # Post-Send
   )

Within each phase, strategies execute in the order they were provided.

Adding strategies at runtime
----------------------------

Beyond the strategies passed to the constructor, you can register
additional strategies at any point before the runner enters its
processing loop.  Each phase exposes an ``.add()`` method:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Phase
     - When it runs
     - Typical use
   * - ``pre_send``
     - Before the message is dispatched.
     - Rate limiting, validation, logging.
   * - ``on_send``
     - During dispatch (wraps the send call).
     - Timeout, retry, jitter.
   * - ``post_send``
     - After a response has been produced.
     - Delay, requeue, metrics collection.

.. code-block:: python

   runner = SenderRunner(
       sender,
       TimeoutStrategy(timeout=5),   # on_send — wraps the call
       RetryStrategy(attempts=3),    # on_send — retries on error
       DelayStrategy(delay=10),      # post_send — pause between sends
   )

   # Register additional strategies after construction
   runner.pre_send.add(RateLimiterStrategy(rate=30, period=60))
   runner.on_send.add(JitterStrategy(attempts=2, delay=1.0))
   runner.post_send.add(RequeueStrategy(cycles=5))

Strategies within each phase execute in insertion order.  The full
pipeline is:

.. code-block:: text

   pre_send[0] → pre_send[1] → … →
   on_send[0]  → on_send[1]  → … →  sender.send_message()
   post_send[0] → post_send[1] → … →
   response returned to runner

.. note::

   Strategies added **after** ``async with runner:`` take effect
   starting from the next queued request.  The currently
   in-flight request is not affected.

Writing a custom strategy
-------------------------

Implement the protocol that matches your intended phase:

Pre-Send Strategy
^^^^^^^^^^^^^^^^^

Inherit from ``BasePreSendStrategy``. Use this to perform actions *before* the
message is sent (e.g., logging, validation, or pre-send delays).

On-Send Strategy
^^^^^^^^^^^^^^^^

Inherit from ``BaseSendStrategy``. Use this to control *how* the message is
sent or to implement retry logic.

Post-Send Strategy
^^^^^^^^^^^^^^^^^^

Inherit from ``BasePostSendStrategy``. Use this to perform actions *after* the
message is sent (e.g., re-queuing or post-send delays).

Rules for custom strategies:

1.  **Always** inherit from the appropriate base class (``BasePreSendStrategy``,
    ``BaseSendStrategy``, or ``BasePostSendStrategy``).
2.  In ``BaseSendStrategy``, **always** check if ``response is not None``
    before sending to avoid double-sending if multiple on-send strategies are
    used.
3.  In ``BasePostSendStrategy``, **always** return a ``MessageResponse``.
4.  Never ``await`` a future returned by ``runner.request()`` --- this causes
    a deadlock. Use ``runner.request() fire-and-forget`` only (like
    ``RequeueStrategy`` does).
