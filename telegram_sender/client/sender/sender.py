import logging
from typing import TYPE_CHECKING, Self

import pyrogram
from pyrogram.errors import RPCError
from tg_devices.generator.generator import DeviceProfileGenerator
from tg_devices.generator.profile import OSProfile
from tg_devices.random.provider import StandardRandomProvider

from telegram_sender.client.sender.protocols import IMessageSender
from telegram_sender.client.sender.proxy import (
    ProxySeq,
    pick_random_proxy,
)
from telegram_sender.client.sender.request import MessageRequest
from telegram_sender.client.sender.resolver import resolve_media
from telegram_sender.client.sender.response import MessageResponse
from telegram_sender.enums.os import OS

if TYPE_CHECKING:
    from types import TracebackType

logger = logging.getLogger(__name__)


class MessageSender(IMessageSender):
    """Telegram message sender backed by a Pyrogram client.

    Generates a randomized device profile per session using
    ``tg-devices`` and dispatches text / media messages through
    the corresponding Pyrogram methods.

    Use as an async context manager to manage the client
    lifecycle::

        async with MessageSender(session="my_session") as s:
            await s.send_message(request)
    """

    def __init__(
        self,
        session: str,
        os: OS = OS.ANDROID,
        device: OSProfile | None = None,
        api_id: int | None = None,
        api_hash: str | None = None,
        proxies: ProxySeq | None = None,
    ) -> None:
        """Initialize the message sender.

        Args:
            session: Pyrogram session name (also used as the
                random seed for device profile generation).
            os: Target OS for the generated device profile.
            device: Optional pre-generated OS profile. If not
                provided, one is generated using the session name.
            api_id: Telegram API application ID.
            api_hash: Telegram API application hash.
            proxies: Proxies sequence or None
        """
        self.session = session
        self.os = os
        self.api_id = api_id
        self.api_hash = api_hash
        self.proxies = proxies
        self._client: pyrogram.Client | None = None

        if device:
            self._device = device
        else:
            device_profile_generator = DeviceProfileGenerator(
            random_provider=StandardRandomProvider(seed=session)
        )
            self._device = device_profile_generator.generate_os_profile(
                os=self.os
            )

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
            try:
                await self._client.stop()
            except ConnectionError:
                pass
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

            proxy = (
                pick_random_proxy(self.proxies, self.session)
                if self.proxies
                else None
            )
            self._client = pyrogram.Client(
                name=self.session,
                api_id=self.api_id,
                api_hash=self.api_hash,
                device_model=self._device.device_model,
                system_version=self._device.system_version,
                app_version=self._device.app_version,
                proxy=proxy,
                sleep_threshold=0
            )
            logger.debug(
                "Created client for session '%s' "
                "(device=%s, system=%s, app=%s)",
                self.session,
                self._device.device_model,
                self._device.system_version,
                self._device.app_version,
            )

        return self._client

    async def __aenter__(self) -> Self:
        client = await self.create_client()
        try:
            await client.start()
        except ConnectionError:
            pass
        logger.info("Client started for session '%s'", self.session)
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def send_message(
        self,
        request: MessageRequest
    ) -> MessageResponse:
        data = request.model_dump(exclude_none=True)
        try:
            if request.media:
                text: str | None = data.pop("text", None)
                method_name, media_kwargs = resolve_media(
                    request.media, text=text
                )
                data.update(media_kwargs)

                logger.debug(
                    "Sending %s to chat_id=%s",
                    type(request.media).__name__,
                    request.chat_id,
                )
                result: (
                    pyrogram.types.Message
                    | list[pyrogram.types.Message]
                    | None
                ) = await getattr(self.client, method_name)(
                    **data
                )
            else:
                logger.debug(
                    "Sending text message to chat_id=%s",
                    request.chat_id,
                )
                result = await self.client.send_message(**data)
        except Exception as err:
            if isinstance(err, RPCError):
                logger.warning(
                    "RPCError sending to chat_id=%s: [%s] %s",
                    request.chat_id,
                    err.CODE,
                    err.MESSAGE,
                )
            else:
                logger.error(
                "Exception sending to chat_id=%s: %s",
                request.chat_id,
                err,
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
