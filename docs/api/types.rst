Types & Enums API
=================

.. module:: telegram_sender.types
.. module:: telegram_sender.enums

OS
--

.. class:: telegram_sender.enums.os.OS

   ``StrEnum`` of supported operating systems for device profile generation.

   .. attribute:: ANDROID
      :value: "Android"

   .. attribute:: WINDOWS
      :value: "Windows"

   .. attribute:: MACOS
      :value: "macOS"

   .. attribute:: LINUX
      :value: "Linux"

BaseType
--------

.. class:: telegram_sender.types.base.BaseType

   Base immutable Pydantic model for all domain types.

   ``model_config``: ``frozen=True``, ``extra="forbid"``,
   ``use_enum_values=True``, ``arbitrary_types_allowed=True``.

MediaType
---------

.. data:: telegram_sender.types.media.MediaType

   Type alias: ``str | BinaryIO``.

   Represents a file path / URL (``str``) or an in-memory binary stream.

Media
-----

.. class:: telegram_sender.types.media.Media

   Base class for all media attachment types.  Extends ``BaseType``.

Photo
^^^^^

.. class:: telegram_sender.types.media.Photo

   Photo attachment.

   :param photo: File path, URL, or binary stream.
   :type photo: MediaType

Video
^^^^^

.. class:: telegram_sender.types.media.Video

   Video attachment.

   :param video: File path, URL, or binary stream.
   :type video: MediaType

Audio
^^^^^

.. class:: telegram_sender.types.media.Audio

   Audio attachment.

   :param audio: File path, URL, or binary stream.
   :type audio: MediaType

Document
^^^^^^^^

.. class:: telegram_sender.types.media.Document

   Document attachment.

   :param document: File path, URL, or binary stream.
   :type document: MediaType

Sticker
^^^^^^^

.. class:: telegram_sender.types.media.Sticker

   Sticker attachment.

   :param sticker: File path, URL, or binary stream.
   :type sticker: MediaType

Animation
^^^^^^^^^

.. class:: telegram_sender.types.media.Animation

   GIF / animation attachment.

   :param animation: File path, URL, or binary stream.
   :type animation: MediaType

Voice
^^^^^

.. class:: telegram_sender.types.media.Voice

   Voice message attachment.

   :param voice: File path, URL, or binary stream.
   :type voice: MediaType

VoiceNote
^^^^^^^^^

.. class:: telegram_sender.types.media.VoiceNote

   Video note (round video) attachment.

   Internally mapped to Pyrogram's ``send_video_note``.

   :param voice_note: File path, URL, or binary stream.
   :type voice_note: MediaType

MediaGroup
^^^^^^^^^^

.. class:: telegram_sender.types.media.MediaGroup

   A group of media items sent as an album.

   Supported item types: ``Photo``, ``Video``, ``Audio``, ``Document``,
   ``Animation``.

   :param media: Sequence of media items.
   :type media: Sequence[Media]
