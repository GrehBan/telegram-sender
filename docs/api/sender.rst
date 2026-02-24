Sender API
==========

.. module:: telegram_sender.client.sender

MessageSender
-------------

.. class:: telegram_sender.client.sender.sender.MessageSender(session, os=OS.ANDROID, api_id=None, api_hash=None)

   Telegram message sender backed by a Pyrogram client.

   Generates a randomized device profile per session using ``tg-devices`` and
   dispatches text / media messages through the corresponding Pyrogram
   methods.

   Use as an async context manager to manage the client lifecycle::

       async with MessageSender(session="my_session") as s:
           await s.send_message(request)

   :param session: Pyrogram session name.  Also used as the deterministic
       seed for device profile generation.
   :param os: Target OS for the generated device profile.
   :param api_id: Telegram API application ID.
   :param api_hash: Telegram API application hash.

   .. attribute:: session
      :type: str

      The session name.

   .. attribute:: os
      :type: tg_devices.enums.os.OS

      Target operating system for device profiles.

   .. attribute:: api_id
      :type: int | None

      Telegram API application ID.

   .. attribute:: api_hash
      :type: str | None

      Telegram API application hash.

   .. property:: client
      :type: pyrogram.Client

      The active Pyrogram client.

      :raises RuntimeError: If the client has not been initialized via the
          async context manager.

   .. method:: close() -> None
      :async:

      Stop the Pyrogram client and release resources.  Only acts if the
      client is currently connected.

   .. method:: create_client(close=True) -> pyrogram.Client
      :async:

      Create (or re-create) the underlying Pyrogram client with a freshly
      generated device profile.

      :param close: If ``True``, close the existing client before creating a
          new one.
      :returns: The created Pyrogram ``Client`` instance.

   .. method:: send_message(request) -> MessageResponse
      :async:

      Send a message described by *request*.

      Dispatches to the appropriate Pyrogram method based on the media type
      attached to the request.  Telegram ``RPCError`` is caught and wrapped
      into the returned ``MessageResponse`` instead of propagating.

      :param request: The message request to send.
      :type request: MessageRequest
      :returns: A ``MessageResponse`` containing either the sent message(s)
          or the captured error.

IMessageSender
--------------

.. class:: telegram_sender.client.sender.protocols.IMessageSender

   ``typing.Protocol`` defining the sender interface.

   Implementations must be usable as async context managers and expose
   ``send_message``.

   .. method:: send_message(request) -> MessageResponse
      :async:
      :abstractmethod:

   .. method:: close() -> None
      :async:
      :abstractmethod:

MessageRequest
--------------

.. class:: telegram_sender.client.sender.request.MessageRequest

   Immutable Pydantic model describing a message to send.

   At least one of ``text`` or ``media`` must be provided.  Extra fields are
   forwarded to the underlying Pyrogram call (e.g. ``parse_mode``,
   ``reply_to_message_id``).

   :param chat_id: Target chat identifier --- numeric ID or username string.
   :param text: Optional text body.  Used as caption when media is attached.
   :param media: Optional media attachment.  Excluded from Pydantic
       serialization and handled separately by the sender.

   .. attribute:: model_config

      ``frozen=True``, ``use_enum_values=True``, ``arbitrary_types_allowed=True``, ``extra="allow"``.

MessageResponse
---------------

.. class:: telegram_sender.client.sender.response.MessageResponse

   Immutable Pydantic model wrapping a send result.

   Exactly one of ``original`` or ``error`` must be provided.

   :param original: The Pyrogram ``Message`` (or list of ``Message`` for
       media groups) returned on success.
   :param error: The ``RPCError`` captured on failure.

   .. attribute:: model_config

      ``frozen=True``, ``use_enum_values=True``, ``arbitrary_types_allowed=True``, ``extra="forbid"``.
