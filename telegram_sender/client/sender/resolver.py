"""Resolve Media objects into Pyrogram-compatible method calls.

Centralises all media-specific dispatch logic (method selection,
caption promotion, field renames, ``InputMedia`` construction)
so that ``MessageSender.send_message`` stays trivial.
"""

from typing import Any, Final, cast

import pyrogram.types

from telegram_sender.types.media import (
    Animation,
    Audio,
    Document,
    Media,
    MediaGroup,
    Photo,
    Sticker,
    Video,
    VideoNote,
    Voice,
)

_METHOD_MAP: Final[dict[type[Media], str]] = {
    Photo: "send_photo",
    Video: "send_video",
    Audio: "send_audio",
    Document: "send_document",
    Sticker: "send_sticker",
    Animation: "send_animation",
    Voice: "send_voice",
    VideoNote: "send_video_note",
    MediaGroup: "send_media_group",
}

_CAPTION_TYPES: Final[frozenset[type[Media]]] = frozenset(
    cast(
        set[type[Media]],
        {Photo, Video, Audio, Document, Animation, Voice},
    )
)

_FIELD_RENAMES: Final[dict[str, str]] = {
    "voice_note": "video_note",
}

_INPUT_MEDIA_MAP: Final[
    dict[
        type[Media],
        type[
            pyrogram.types.InputMediaPhoto
            | pyrogram.types.InputMediaVideo
            | pyrogram.types.InputMediaAudio
            | pyrogram.types.InputMediaDocument
            | pyrogram.types.InputMediaAnimation
        ],
    ]
] = {
    Photo: pyrogram.types.InputMediaPhoto,
    Video: pyrogram.types.InputMediaVideo,
    Audio: pyrogram.types.InputMediaAudio,
    Document: pyrogram.types.InputMediaDocument,
    Animation: pyrogram.types.InputMediaAnimation,
}


def resolve_media(
    media: Media,
    text: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Resolve a ``Media`` object into a Pyrogram method name
    and keyword arguments.

    Handles caption promotion, field renames, and media-group
    construction from the **original typed objects** (not from
    post-``model_dump`` dicts), so no fields are silently lost.

    Args:
        media: The media attachment to resolve.
        text: Optional message text.  Promoted to ``caption``
            for media types that support it; silently dropped
            for those that do not (e.g. ``Sticker``).

    Returns:
        A ``(method_name, kwargs)`` tuple.  Merge *kwargs* into
        the base request data and call
        ``getattr(client, method_name)(**merged)``.

    Raises:
        TypeError: If the media type is unsupported.
        ValueError: If a ``MediaGroup`` contains no items.
    """
    media_type = type(media)

    method = _METHOD_MAP.get(media_type)
    if method is None:
        raise TypeError(
            f"Unsupported media type: {media_type.__name__}"
        )

    if isinstance(media, MediaGroup):
        return method, {
            "media": _resolve_media_group(media),
        }

    kwargs = media.model_dump(exclude_none=True)

    for old_key, new_key in _FIELD_RENAMES.items():
        if old_key in kwargs:
            kwargs[new_key] = kwargs.pop(old_key)

    if text and media_type in _CAPTION_TYPES:
        kwargs["caption"] = text

    return method, kwargs


def _resolve_media_group(
    group: MediaGroup,
) -> list[
    pyrogram.types.InputMediaPhoto
    | pyrogram.types.InputMediaVideo
    | pyrogram.types.InputMediaAudio
    | pyrogram.types.InputMediaDocument
    | pyrogram.types.InputMediaAnimation
]:
    """Build Pyrogram ``InputMedia*`` objects from a
    ``MediaGroup``.

    Each item is constructed from the **original** ``Media``
    subclass via ``model_dump``, preserving every field.

    Raises:
        TypeError: If an item type cannot be mapped.
        ValueError: If the group is empty after processing.
    """
    items: list[
        pyrogram.types.InputMediaPhoto
        | pyrogram.types.InputMediaVideo
        | pyrogram.types.InputMediaAudio
        | pyrogram.types.InputMediaDocument
        | pyrogram.types.InputMediaAnimation
    ] = []

    for item in group.media:
        input_cls = _INPUT_MEDIA_MAP.get(type(item))
        if input_cls is None:
            raise TypeError(
                f"Unsupported media group item type: "
                f"{type(item).__name__}"
            )
        items.append(
            input_cls(**item.model_dump(exclude_none=True))
        )

    if not items:
        raise ValueError(
            "MediaGroup must contain at least one item"
        )

    return items