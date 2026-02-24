Quickstart
==========

This guide walks through sending your first message.

Minimal example
---------------

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
               request=MessageRequest(
                   chat_id="me",
                   text="Hello from telegram-sender!",
               )
           )
           async for response in runner.results():
               print(response)


   asyncio.run(main())

On first run Pyrogram will prompt for your phone number and verification code
to create a session file.

Step-by-step breakdown
----------------------

1. **Create a sender** --- ``MessageSender`` wraps a Pyrogram client.  The
   ``session`` string is both the session file name and the seed for device
   profile randomization.

2. **Create a runner** --- ``SenderRunner`` accepts the sender and any number
   of strategies.  Strategies are composed into a pipeline via
   ``CompositeStrategy`` and executed in order for every request.

3. **Enter the context** --- ``async with runner:`` starts the Pyrogram client
   and spawns a background ``asyncio`` task that processes the request queue.

4. **Enqueue requests** --- ``await runner.request(req)`` puts a
   ``MessageRequest`` into the queue and returns a ``Future`` that resolves
   once the request is handled.

5. **Consume results** --- ``async for response in runner.results():`` yields
   ``MessageResponse`` objects as they become available.  The generator
   terminates when the runner is stopped and the response queue is empty.

Sending media
-------------

Attach a media object to the request via the ``media`` parameter:

.. code-block:: python

   from telegram_sender.types.media import Photo

   request = MessageRequest(
       chat_id="me",
       text="Check this out!",          # becomes the caption
       media=Photo(photo="/path/to/image.jpg"),
   )

All media types (``Photo``, ``Video``, ``Audio``, ``Document``, ``Sticker``,
``Animation``, ``Voice``, ``VoiceNote``) accept a file path, URL, or binary
stream.

Sending an album
^^^^^^^^^^^^^^^^

Use ``MediaGroup`` with a sequence of media items:

.. code-block:: python

   from telegram_sender.types.media import MediaGroup, Photo, Video

   request = MessageRequest(
       chat_id="me",
       media=MediaGroup(
           media=[
               Photo(photo="/path/to/a.jpg"),
               Video(video="/path/to/b.mp4"),
           ]
       ),
   )

Choosing a device profile
--------------------------

By default the sender emulates an Android device.  Pass the ``os`` parameter
to change this:

.. code-block:: python

   from telegram_sender.enums.os import OS

   sender = MessageSender(
       session="my_session",
       os=OS.MACOS,
       api_id=12345678,
       api_hash="...",
   )

Supported values: ``OS.ANDROID``, ``OS.WINDOWS``, ``OS.MACOS``, ``OS.LINUX``.

Using the sender without a runner
---------------------------------

If you don't need strategies or queue-based processing, use ``MessageSender``
directly:

.. code-block:: python

   async with MessageSender(session="s", api_id=..., api_hash="...") as s:
       response = await s.send_message(
           MessageRequest(chat_id="me", text="Direct send")
       )
       if response.error:
           print("Failed:", response.error)
       else:
           print("Sent:", response.original)

Handling errors
---------------

``MessageSender.send_message()`` catches Telegram ``RPCError`` and wraps it
into the ``MessageResponse.error`` field instead of raising:

.. code-block:: python

   async for response in runner.results():
       if response.error:
           print(f"Error [{response.error.CODE}]: {response.error.MESSAGE}")
       else:
           print(f"Message ID: {response.original.id}")

``TimeoutError`` from ``TimeoutStrategy`` and all non-RPC exceptions propagate
to the runner, which catches them and sets the future's exception.

Logging
-------

All modules use standard ``logging`` with ``__name__`` as the logger name.
Enable debug output to see the full pipeline:

.. code-block:: python

   import logging

   logging.basicConfig(
       level=logging.DEBUG,
       format="%(asctime)s %(levelname)s %(name)s %(message)s",
   )
