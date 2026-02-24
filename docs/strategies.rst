Strategies Guide
================

Strategies are composable behaviours applied to every message request.  They
are executed as a **sequential pipeline** by ``CompositeStrategy``: the
response from each strategy is forwarded to the next.

Built-in strategies
-------------------

DelayStrategy
^^^^^^^^^^^^^

Introduces a fixed pause after each send.

.. code-block:: python

   from telegram_sender.client.strategies.delay import DelayStrategy

   DelayStrategy(delay=5.0)   # 5-second delay

If the response contains an ``RPCError`` whose ``value`` is numeric (e.g. a
flood-wait duration), that value overrides the configured delay.

RequeueStrategy
^^^^^^^^^^^^^^^

Re-enqueues the same request into the runner's queue after each send, causing
it to be sent again.

.. code-block:: python

   from telegram_sender.client.strategies.requeue import RequeueStrategy

   RequeueStrategy()           # infinite re-enqueues
   RequeueStrategy(cycles=10)  # stop after 10 total re-enqueues

.. important::

   The ``cycles`` counter is **global** to the strategy instance, not
   per-request.  Once the limit is reached, no further requests of any kind
   will be re-enqueued.  For infinite looping use ``cycles=-1`` (the default).

RetryStrategy
^^^^^^^^^^^^^

Retries the send on error with a fixed delay between attempts.

.. code-block:: python

   from telegram_sender.client.strategies.retry import RetryStrategy

   RetryStrategy(attempts=3, delay=2.0)

If the error carries a numeric ``value`` (e.g. flood-wait seconds), it is
used instead of the fixed ``delay``.

JitterStrategy
^^^^^^^^^^^^^^

Retries with exponential backoff plus random jitter:

.. math::

   \text{delay} = \text{base} \times 2^{\text{attempt}} + \text{uniform}(0,\; \text{backoff} \times \text{jitter\_ratio})

.. code-block:: python

   from telegram_sender.client.strategies.jitter import JitterStrategy

   JitterStrategy(attempts=5, delay=1.0, jitter_ratio=0.5)

RateLimiterStrategy
^^^^^^^^^^^^^^^^^^^

Sliding-window rate limiter that ensures no more than ``rate`` requests are
sent within any rolling ``period``.

.. code-block:: python

   from telegram_sender.client.strategies.rate_limit import RateLimiterStrategy

   RateLimiterStrategy(rate=20, period=60.0)  # 20 req / 60 s

When the limit is reached the strategy sleeps until the oldest timestamp
expires from the window.

TimeoutStrategy
^^^^^^^^^^^^^^^

Wraps the send call with ``asyncio.wait_for``.  Raises ``TimeoutError`` if
the send does not complete in time.

.. code-block:: python

   from telegram_sender.client.strategies.timeout import TimeoutStrategy

   TimeoutStrategy(timeout=10.0)

.. warning::

   ``TimeoutStrategy`` **must be placed first** in the pipeline.  On timeout
   it raises ``TimeoutError`` which skips all subsequent strategies.  The
   runner catches the exception and sets it on the request's ``Future``.

Composing strategies
--------------------

Pass multiple strategies to ``SenderRunner`` --- they execute left-to-right:

.. code-block:: python

   runner = SenderRunner(
       sender,
       RequeueStrategy(),           # 1. send + re-enqueue
       DelayStrategy(delay=10),     # 2. sleep 10 s
   )

The first strategy in the chain receives ``response=None`` and is responsible
for calling ``sender.send_message()``.  Each subsequent strategy receives the
response from the previous one and adds its behaviour without sending again.

Pipeline examples
^^^^^^^^^^^^^^^^^

**Send once with rate-limiting and delay:**

.. code-block:: python

   runner = SenderRunner(
       sender,
       RateLimiterStrategy(rate=30, period=60),
       DelayStrategy(delay=2),
   )

**Send with retry + jitter, then delay:**

.. code-block:: python

   runner = SenderRunner(
       sender,
       JitterStrategy(attempts=3, delay=1.0),
       DelayStrategy(delay=5),
   )

**Timeout + infinite requeue + delay:**

.. code-block:: python

   runner = SenderRunner(
       sender,
       TimeoutStrategy(timeout=10),   # must be first
       RequeueStrategy(),
       DelayStrategy(delay=5),
   )

Writing a custom strategy
--------------------------

Implement the ``ISendStrategy`` protocol:

.. code-block:: python

   from telegram_sender.client.runner.protocols import ISenderRunner
   from telegram_sender.client.sender.protocols import IMessageSender
   from telegram_sender.client.sender.request import MessageRequest
   from telegram_sender.client.sender.response import MessageResponse


   class LoggingStrategy:
       """Logs every request/response pair."""

       async def __call__(
           self,
           sender: IMessageSender,
           runner: ISenderRunner,
           request: MessageRequest,
           response: MessageResponse | None = None,
       ) -> MessageResponse:
           if response is None:
               response = await sender.send_message(request)
           if response.error:
               print(f"FAIL chat_id={request.chat_id}: {response.error}")
           else:
               print(f"OK   chat_id={request.chat_id}")
           return response

Rules for custom strategies:

1. Accept ``response: MessageResponse | None = None``.
2. If ``response is None``, call ``sender.send_message(request)`` yourself.
3. If ``response is not None``, **do not send again** --- just apply your
   behaviour and return.
4. Always return a ``MessageResponse``.
5. Never ``await`` a future returned by ``runner.request()`` --- this causes
   a deadlock.  Use ``runner.request()`` fire-and-forget only (like
   ``RequeueStrategy`` does).
