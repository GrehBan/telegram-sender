from collections.abc import Sequence
from typing import BinaryIO, TypeAlias, TypeVar

from telegram_sender.types.base import BaseType

MediaType: TypeAlias = str | BinaryIO  # noqa: UP040

MediaT = TypeVar("MediaT", bound="Media")


class Media(BaseType):
    """Base class for all media attachment types."""


class Photo(Media):
    """Photo attachment.

    Attributes:
        photo: File path, URL, or binary stream of the photo.
    """

    photo: MediaType


class Video(Media):
    """Video attachment.

    Attributes:
        video: File path, URL, or binary stream of the video.
    """

    video: MediaType


class Audio(Media):
    """Audio attachment.

    Attributes:
        audio: File path, URL, or binary stream of the audio.
    """

    audio: MediaType


class Document(Media):
    """Document attachment.

    Attributes:
        document: File path, URL, or binary stream of the
            document.
    """

    document: MediaType


class Sticker(Media):
    """Sticker attachment.

    Attributes:
        sticker: File path, URL, or binary stream of the
            sticker.
    """

    sticker: MediaType


class Animation(Media):
    """GIF / animation attachment.

    Attributes:
        animation: File path, URL, or binary stream of the
            animation.
    """

    animation: MediaType


class Voice(Media):
    """Voice message attachment.

    Attributes:
        voice: File path, URL, or binary stream of the voice
            message.
    """

    voice: MediaType


class VideoNote(Media):
    """Video note (round video) attachment.

    Attributes:
        video_note: File path, URL, or binary stream of the
            video note.
    """

    video_note: MediaType


class MediaGroup(Media):
    """A group of media items sent as an album.

    Attributes:
        media: Sequence of media items to include in the album.
    """

    media: Sequence[Media]