===============
telegram-sender
===============

A strategy-driven, async-first Telegram message sending library built on
`pyrofork <https://github.com/Mayuri-Chan/pyrofork>`_ with automatic device
profile randomization.

.. list-table::
   :widths: 20 80

   * - **Python**
     - >= 3.14
   * - **License**
     - MIT
   * - **Telegram client**
     - pyrofork (Pyrogram fork)
   * - **Device profiles**
     - `tg-devices <https://github.com/GrehBan/tg-devices>`_

Features
--------

* **Strategy pipeline** --- compose retry, delay, rate-limit, timeout, jitter
  and requeue behaviours in any combination.
* **Device fingerprinting** --- every session gets a deterministic yet
  randomized device profile (model, OS version, app version).
* **Pydantic v2 models** --- immutable, validated ``MessageRequest`` /
  ``MessageResponse`` objects.
* **Protocol-based design** --- all interfaces are ``typing.Protocol`` classes,
  easy to extend and mock.
* **Full media support** --- text, photo, video, audio, document, sticker,
  animation, voice, video note, and media groups (albums).

Installation
------------

.. code-block:: bash

   git clone https://github.com/GrehBan/telegram-sender.git
   cd telegram-sender
   uv sync

Requires `uv <https://docs.astral.sh/uv/>`_ and a Telegram API application
(``api_id`` / ``api_hash``) from `my.telegram.org <https://my.telegram.org>`_.

Quick start
-----------

.. code-block:: python

   import asyncio

   from telegram_sender.client.runner.runner import SenderRunner
   from telegram_sender.client.sender.request import MessageRequest
   from telegram_sender.client.sender.sender import MessageSender
   from telegram_sender.client.strategies.delay import DelayStrategy
   from telegram_sender.client.strategies.requeue import RequeueStrategy


   async def main() -> None:
       sender = MessageSender(
           session="my_session",
           api_id=12345678,
           api_hash="abcdef1234567890abcdef1234567890",
       )
       runner = SenderRunner(
           sender,
           RequeueStrategy(),      # re-enqueue infinitely
           DelayStrategy(delay=10), # 10 s pause between sends
       )

       async with runner:
           await runner.request(
               request=MessageRequest(chat_id="me", text="Hello!")
           )
           async for response in runner.results():
               print(response)


   asyncio.run(main())

Sending media
^^^^^^^^^^^^^

.. code-block:: python

   from telegram_sender.types.media import Photo

   request = MessageRequest(
       chat_id="me",
       text="Check this out!",
       media=Photo(photo="/path/to/image.jpg"),
   )

Available strategies
--------------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Strategy
     - Description
   * - ``DelayStrategy``
     - Fixed pause after each send.  Respects flood-wait values.
   * - ``RequeueStrategy``
     - Fire-and-forget re-enqueue for repeated sending.
   * - ``RetryStrategy``
     - Retry on error with a fixed delay.
   * - ``JitterStrategy``
     - Retry with exponential backoff + random jitter.
   * - ``RateLimiterStrategy``
     - Sliding-window rate limiter (N requests per M seconds).
   * - ``TimeoutStrategy``
     - ``asyncio.wait_for`` wrapper.  Must be first in the pipeline.

Strategies are composed left-to-right:

.. code-block:: python

   runner = SenderRunner(
       sender,
       TimeoutStrategy(timeout=10),
       RequeueStrategy(),
       DelayStrategy(delay=5),
   )

Architecture
------------

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

See ``docs/architecture.rst`` for the full design document.

Development
-----------

.. code-block:: bash

   uv sync --group dev

   # Lint
   uv run ruff check telegram_sender/

   # Format
   uv run ruff format telegram_sender/

   # Type check
   uv run mypy telegram_sender/

Documentation
-------------

Full documentation lives in the ``docs/`` directory:

* `docs/installation.rst <docs/installation.rst>`_ --- installation guide
* `docs/quickstart.rst <docs/quickstart.rst>`_ --- tutorial with examples
* `docs/architecture.rst <docs/architecture.rst>`_ --- design and data flow
* `docs/strategies.rst <docs/strategies.rst>`_ --- strategy guide and custom
  strategies
* `docs/api/ <docs/api/>`_ --- complete API reference
* `docs/contributing.rst <docs/contributing.rst>`_ --- code style, tooling,
  project layout

License
-------

MIT --- see `LICENSE <LICENSE>`_.
