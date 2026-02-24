from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from telegram_sender.types.media import Media


class MessageRequest(BaseModel):
    """Immutable request describing a message to send.

    At least one of ``text`` or ``media`` must be provided.
    Extra fields are forwarded to the underlying Pyrogram call.

    Attributes:
        chat_id: Target chat identifier (numeric ID or username).
        text: Optional text body of the message.
        media: Optional media attachment (excluded from
            serialization, handled separately by the sender).
    """

    model_config = ConfigDict(
        frozen=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
        extra="allow"
    )

    chat_id: int | str
    text: str | None = None
    media: Media | None = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def validate_request_signature(self) -> Self:
        """Validate that at least ``text`` or ``media`` is set."""
        if self.text is None and self.media is None:
            raise ValueError("Either 'text' or 'media' must be provided")
        return self
