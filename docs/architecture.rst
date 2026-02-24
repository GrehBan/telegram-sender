Architecture
============

This document describes the high-level design of telegram-sender.

Overview
--------

The library is built around three layers:

.. code-block:: text

   MessageRequest
        |
        v
   +-----------+       +----------------+       +------------------+
   |  Runner   | ----> |  Strategies    | ----> |     Sender       |
   | (queue +  |       | (pipeline of   |       | (Pyrogram client |
   |  loop)    |       |  behaviours)   |       |  + device prof.) |
   +-----------+       +----------------+       +------------------+
        |                                               |
        v                                               v
   MessageResponse  <----------------------------------+

1. **MessageSender** --- owns the Pyrogram ``Client``, generates a random
   device profile, dispatches requests to the correct Pyrogram method.
2. **SenderRunner** --- async queue-based orchestrator that pulls requests,
   passes them through the strategy pipeline, and collects responses.
3. **Strategies** --- composable behaviours (delay, retry, requeue, rate-limit,
   timeout, jitter) executed as a sequential pipeline.

Data flow
---------

1. User calls ``runner.request(MessageRequest(...))``
2. The request + a ``Future`` are placed in the ``_requests`` queue.
3. The background task (``run()``) pulls the pair from the queue.
4. ``_handle_request()`` invokes the strategy pipeline (or the sender
   directly if no strategies are configured).
5. The first strategy in the chain calls ``sender.send_message(request)``
   and returns a ``MessageResponse``.
6. Each subsequent strategy receives the response and can add behaviour
   (sleep, re-enqueue, rate-limit) without sending again.
7. The final response is placed in the ``_responses`` queue and the
   ``Future`` is resolved.
8. The user receives responses via ``runner.results()`` async generator.

Strategy pipeline
-----------------

Strategies implement the ``ISendStrategy`` protocol:

.. code-block:: python

   class ISendStrategy(Protocol):
       async def __call__(
           self,
           sender: IMessageSender,
           runner: ISenderRunner,
           request: MessageRequest,
           response: MessageResponse | None = None,
       ) -> MessageResponse: ...

``CompositeStrategy`` chains strategies sequentially, forwarding the response
from each strategy to the next:

.. code-block:: python

   for strategy in self.strategies:
       response = await strategy(sender, runner, request, response)

Key rule: **when** ``response is None`` **the strategy is the first in the
chain and must call** ``sender.send_message()`` **itself**.  Otherwise it
reuses the existing response.

This design prevents:

* **Duplicate sends** --- only the first strategy sends.
* **Deadlocks** --- strategies call the sender directly instead of
  re-entering the runner's queue and waiting for the future.

Protocol-based interfaces
-------------------------

All core contracts are ``typing.Protocol`` classes:

``IMessageSender``
   Async context manager + ``send_message(request) -> MessageResponse``.

``ISenderRunner``
   Async context manager + ``request()``, ``results()``, ``result()``,
   ``run()``.

``ISendStrategy``
   Callable ``(sender, runner, request, response?) -> MessageResponse``.

This makes it straightforward to substitute implementations for testing or
to add custom senders / runners.

Device profile generation
-------------------------

``MessageSender`` uses ``tg-devices`` to generate a plausible device
fingerprint (model, system version, app version) for the Pyrogram client.
The ``session`` string is used as a deterministic seed via
``StandardRandomProvider(seed=session)``, so the same session always produces
the same device profile.

The target OS is configurable via the ``OS`` enum (``ANDROID``, ``WINDOWS``,
``MACOS``, ``LINUX``).  Defaults to ``ANDROID``.

Immutable models
----------------

All request / response / media objects are **Pydantic v2 models** with
``frozen=True``:

* ``MessageRequest`` --- requires ``text`` and/or ``media``, accepts extra
  fields forwarded to Pyrogram.
* ``MessageResponse`` --- wraps either a Pyrogram ``Message`` or an
  ``RPCError``.
* ``Media`` subtypes --- ``Photo``, ``Video``, ``Audio``, ``Document``,
  ``Sticker``, ``Animation``, ``Voice``, ``VoiceNote``, ``MediaGroup``.

Immutability guarantees that objects can be safely shared and re-enqueued
without risk of mutation.

Error handling
--------------

Errors are handled at two levels:

1. **Sender level** --- ``MessageSender.send_message()`` catches
   ``RPCError`` from Pyrogram and wraps it into
   ``MessageResponse(error=err)`` instead of raising.

2. **Runner level** --- ``SenderRunner._handle_request()`` catches **all**
   exceptions from the strategy pipeline.  The exception is set on the
   request's ``Future`` so the caller can observe it.

``TimeoutStrategy`` is a special case --- it re-raises ``TimeoutError``,
which propagates through the pipeline and is caught by the runner.  For this
reason ``TimeoutStrategy`` must be placed **first** in the pipeline.

Concurrency model
-----------------

* ``SenderRunner`` runs a **single background task** that processes the
  request queue sequentially.  Only one request is in-flight at a time.
* All strategies are invoked within this single task, so shared mutable state
  (e.g. ``RateLimiterStrategy._timestamps``) is safe from concurrent access
  as long as strategy instances are not shared across multiple runners.
* ``RequeueStrategy`` uses fire-and-forget: it calls ``runner.request()`` to
  place a new request in the queue but does **not** await the returned future,
  avoiding deadlocks.

Graceful shutdown
-----------------

1. ``runner.close()`` sets the ``_stop_event``.
2. The background task exits its main loop and calls ``_drain()`` to process
   any remaining requests in the queue (including re-enqueued ones).
3. ``runner.__aexit__`` calls ``close()`` then ``sender.__aexit__()`` to
   properly disconnect the Pyrogram client.
