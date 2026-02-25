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
   | (queue +  |       | (Pre/On/Post   |       | (Pyrogram client |
   |  loop)    |       |  pipeline)     |       |  + device prof.) |
   +-----------+       +----------------+       +------------------+
        |                                               |
        v                                               v
   MessageResponse  <----------------------------------+

1. **MessageSender** --- owns the Pyrogram ``Client``, generates a random
   device profile, and dispatches requests to the correct Pyrogram method.
   Delegates media resolution logic to ``resolve_media`` and proxy
   selection to ``pick_random_proxy``.
2. **SenderRunner** --- async queue-based orchestrator that pulls requests,
   passes them through the strategy pipeline phases, and collects responses.
3. **Strategies** --- composable behaviours (delay, retry, requeue, rate-limit,
   timeout, jitter) organized into three distinct execution phases.

.. note::

   The **Media Resolver** (``resolve_media``) centralises all media-specific
   dispatch logic (method selection, caption promotion, field renames,
   ``InputMedia`` construction) so that the core sender remains simple and
   easy to maintain.

   The **Proxy Manager** (``proxy.py``) provides typed configurations and
   deterministic selection, ensuring that each session remains bound to the
   same proxy if a list is provided.
Data flow
---------

1. User calls ``runner.request(MessageRequest(...))``
2. The request + a ``Future`` are placed in the ``_requests`` queue.
3. The background task (``run()``) pulls the pair from the queue.
4. ``_handle_request()`` invokes the three-phase strategy pipeline:
    a. **Pre-Send** strategies are executed first (no response available).
       Used for preparation, validation, or rate limiting.
    b. **On-Send** strategy is executed. If multiple are provided, the first
       produces a ``MessageResponse``. If none are provided, the runner
       calls ``sender.send_message()`` directly.
    c. **Post-Send** strategies receive the response and can add behaviour
       (sleep, retry, re-enqueue).
5. The final response is placed in the ``_responses`` queue and the
   ``Future`` is resolved.
6. The user receives responses via ``runner.results()`` async generator.

Strategy pipeline
-----------------

Strategies are categorized by the protocol they implement:

Pre-Send (``IPreSendStrategy``)
    Executed before sending. Returns ``None``.

On-Send (``ISendStrategy``)
    Responsible for producing a ``MessageResponse``.
    **Key rule**: always check if ``response is not None`` before sending.

Post-Send (``IPostSendStrategy``)
    Executed after sending. Receives and returns a ``MessageResponse``.

Each phase uses a corresponding ``Composite*Strategy`` to chain its
strategies.

Protocol-based interfaces
-------------------------

All core contracts are ``typing.Protocol`` classes:

``IMessageSender``
   Async context manager + ``send_message(request) -> MessageResponse``.

``ISenderRunner``
   Async context manager + ``request()``, ``results()``, ``result()``,
   ``run()``.

``IPreSendStrategy``, ``ISendStrategy``, ``IPostSendStrategy``
   The three phase protocols defining the strategy pipeline.

Device profile generation
-------------------------

``MessageSender`` uses ``tg-devices`` to generate a plausible device
fingerprint (model, system version, app version) for the Pyrogram client.
The ``session`` string is used as a deterministic seed via
``StandardRandomProvider(seed=session)``, so the same session always produces
the same device profile.

The target OS is configurable via the ``OS`` enum (``ANDROID``, ``WINDOWS``,
``MACOS``, ``LINUX``). Defaults to ``ANDROID``.

Immutable models
----------------

All request / response / media objects are **Pydantic v2 models** with
``frozen=True``:

* ``MessageRequest`` --- requires ``text`` and/or ``media``, accepts extra
  fields forwarded to Pyrogram.
* ``MessageResponse`` --- wraps either a Pyrogram ``Message`` or an
  ``RPCError``.
* ``Media`` subtypes --- ``Photo``, ``Video``, ``Audio``, ``Document``,
  ``Sticker``, ``Animation``, ``Voice``, ``VideoNote``, ``MediaGroup``.

Immutability guarantees that objects can be safely shared and re-enqueued
without risk of mutation.

Error handling
--------------

Errors are handled at two levels:

1. **Sender level** --- ``MessageSender.send_message()`` catches
   ``RPCError`` from Pyrogram and wraps it into
   ``MessageResponse(error=err)`` instead of raising.

2. **Runner level** --- ``SenderRunner._handle_request()`` catches **all**
   exceptions from the strategy pipeline. The exception is set on the
   request's ``Future`` so the caller can observe it.

``TimeoutStrategy`` (On-Send) raises ``TimeoutError``, which propagates
through the pipeline and is caught by the runner.

Concurrency model
-----------------

* ``SenderRunner`` runs a **single background task** that processes the
  request queue sequentially. Only one request is in-flight at a time.
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
