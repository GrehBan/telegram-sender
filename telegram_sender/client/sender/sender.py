import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Self

import pyrogram
from pyrogram.errors import RPCError
from tg_devices.enums import os as device_os
from tg_devices.generator.generator import DeviceProfileGenerator
from tg_devices.random.provider import StandardRandomProvider

from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.enums.os import OS
from telegram_sender.types.media import (
    Animation,
    Audio,
    Document,
    Media,
    MediaGroup,
    Photo,
    Sticker,
    Video,
    Voice,
    VoiceNote,
)

if TYPE_CHECKING:
    from types import TracebackType

logger = logging.getLogger(__name__)


class MessageSender:
    """Telegram message sender backed by a Pyrogram client.

    Generates a randomized device profile per session using
    ``tg-devices`` and dispatches text / media messages through
    the corresponding Pyrogram methods.

    Use as an async context manager to manage the client
    lifecycle::

        async with MessageSender(session="my_session") as s:
            await s.send_message(request)

    Args:
        session: Pyrogram session name (also used as the
            random seed for device profile generation).
        os: Target OS for the generated device profile.
        api_id: Telegram API application ID.
        api_hash: Telegram API application hash.
    """

    def __init__(
        self,
        session: str,
        os: OS = OS.ANDROID,
        api_id: int | None = None,
        api_hash: str | None = None,
    ) -> None:
        self.device_profile_generator = DeviceProfileGenerator(
            random_provider=StandardRandomProvider(seed=session)
        )
        
        self.session = session
        self.os = device_os.OS(os.value)
        self.api_id = api_id
        self.api_hash = api_hash
        self._client: pyrogram.Client | None = None

        self._send_media_map: dict[
            type[Media],
            Callable[
                [dict[str, Any]],
                Awaitable[
                    pyrogram.types.Message | 
                    list[pyrogram.types.Message] | 
                    None
                ]
            ]
        ] = {
            Photo: self._send_photo,
            Video: self._send_video,
            Audio: self._send_audio,
            Document: self._send_document,
            Sticker: self._send_sticker,
            Animation: self._send_animation,
            Voice: self._send_voice,
            VoiceNote: self._send_voice_note,
            MediaGroup: self._send_media_group,
        }
    
    @property
    def client(self) -> pyrogram.Client:
        """Return the active Pyrogram client.

        Raises:
            RuntimeError: If the client has not been
                initialized via the async context manager.
        """
        if not self._client:
            raise RuntimeError(
                "Client not initialized "
                f"use 'async with {self.__class__.__name__}():'"
                )
        return self._client

    async def close(self) -> None:
        """Stop the Pyrogram client and release resources."""
        if self._client and self._client.is_connected:
            await self._client.stop()
            logger.debug("Client stopped for session '%s'", self.session)
        self._client = None
    
    async def create_client(
        self, close: bool = True
    ) -> pyrogram.Client:
        """Create (or re-create) the underlying Pyrogram client.

        Args:
            close: If ``True``, close the existing client
                before creating a new one.

        Returns:
            The newly created (or existing) Pyrogram client.
        """
        if close:
            await self.close()

        if not self._client or not self._client.is_connected:

            device = self.device_profile_generator.generate_os_profile(
                os=self.os
            )
            self._client = pyrogram.Client(
                name=self.session,
                api_id=self.api_id,
                api_hash=self.api_hash,
                device_model=device.device_model,
                system_version=device.system_version,
                app_version=device.app_version,
                sleep_threshold=0
            )
            logger.debug(
                "Created client for session '%s' "
                "(device=%s, system=%s, app=%s)",
                self.session,
                device.device_model,
                device.system_version,
                device.app_version,
            )

        return self._client

    async def __aenter__(self) -> Self:
        client = await self.create_client()
        await client.start()
        logger.info("Client started for session '%s'", self.session)
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def _send_photo(
        self,
        data: dict[str, Any]
    ) -> pyrogram.types.Message | None:
        if "text" in data:
            data["caption"] = data.pop("text")
        return await self.client.send_photo(**data)

    async def _send_video(
        self,
        data: dict[str, Any]
    ) -> pyrogram.types.Message | None:
        if "text" in data:
            data["caption"] = data.pop("text")
        return await self.client.send_video(**data)

    async def _send_audio(
        self,
        data: dict[str, Any]
    ) -> pyrogram.types.Message | None:
        if "text" in data:
            data["caption"] = data.pop("text")
        return await self.client.send_audio(**data)

    async def _send_document(
        self,
        data: dict[str, Any]
    ) -> pyrogram.types.Message | None:
        if "text" in data:
            data["caption"] = data.pop("text")
        return await self.client.send_document(**data)

    async def _send_sticker(
        self,
        data: dict[str, Any]
    ) -> pyrogram.types.Message | None:
        return await self.client.send_sticker(**data)

    async def _send_animation(
        self,
        data: dict[str, Any]
    ) -> pyrogram.types.Message | None:
        if "text" in data:
            data["caption"] = data.pop("text")
        return await self.client.send_animation(**data)

    async def _send_voice(
        self,
        data: dict[str, Any]
    ) -> pyrogram.types.Message | None:
        if "text" in data:
            data["caption"] = data.pop("text")
        return await self.client.send_voice(**data)

    async def _send_voice_note(
        self,
        data: dict[str, Any]
    ) -> pyrogram.types.Message | None:
        if "voice_note" in data:
            data["video_note"] = data.pop("voice_note")
        return await self.client.send_video_note(**data)

    async def _send_media_group(
        self,
        data: dict[str, Any]
    ) -> list[pyrogram.types.Message] | None:
        media: list[
            pyrogram.types.InputMediaPhoto
            | pyrogram.types.InputMediaVideo
            | pyrogram.types.InputMediaAudio
            | pyrogram.types.InputMediaDocument
            | pyrogram.types.InputMediaAnimation
        ] = []
        for item in data.pop("media", []):
            if "photo" in item:
                media.append(pyrogram.types.InputMediaPhoto(item["photo"]))
            elif "video" in item:
                media.append(pyrogram.types.InputMediaVideo(item["video"]))
            elif "audio" in item:
                media.append(pyrogram.types.InputMediaAudio(item["audio"]))
            elif "document" in item:
                media.append(pyrogram.types.InputMediaDocument(item["document"]))
            elif "animation" in item:
                media.append(pyrogram.types.InputMediaAnimation(item["animation"]))
        
        if not media:
            raise ValueError("MediaGroup must contain at least one media item")

        return await self.client.send_media_group(media=media, **data)

    async def _send_text_message(
        self,
        data: dict[str, Any]
    ) -> pyrogram.types.Message | None:
        return await self.client.send_message(**data)

    async def send_message(
        self,
        request: MessageRequest
    ) -> MessageResponse:
        """Send a message described by *request*.

        Dispatches to the appropriate Pyrogram method based on
        the media type. ``RPCError`` is caught and wrapped into
        the returned ``MessageResponse``.

        Args:
            request: The message request to send.

        Returns:
            A response containing either the sent message(s)
            or the captured error.
        """
        data = request.model_dump(exclude_none=True)
        try:
            if request.media:
                media_type = type(request.media).__name__
                logger.debug(
                    "Sending %s to chat_id=%s",
                    media_type,
                    request.chat_id,
                )
                data.update(request.media.model_dump(exclude_none=True))
                result = await self._send_media_map[type(request.media)](data)
            else:
                logger.debug(
                    "Sending text message to chat_id=%s",
                    request.chat_id,
                )
                result = await self._send_text_message(data)
        except RPCError as err:
            logger.warning(
                "RPCError sending to chat_id=%s: [%s] %s",
                request.chat_id,
                err.CODE,
                err.MESSAGE,
            )
            return MessageResponse(
                original=None,
                error=err
            )

        logger.debug(
            "Message sent successfully to chat_id=%s",
            request.chat_id,
        )
        return MessageResponse(
            original=result,
        )
