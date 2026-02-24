from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator
from pyrogram.errors import RPCError
from pyrogram.types import Message


class MessageResponse(BaseModel):
    """Immutable result of a send attempt.

    Exactly one of ``original`` or ``error`` must be provided.

    Attributes:
        original: The Pyrogram ``Message`` (or list of messages
            for media groups) returned on success.
        error: The ``RPCError`` captured on failure.
    """

    model_config = ConfigDict(
        frozen=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
        extra="forbid"
    )

    original: Message | list[Message] | None = None
    error: RPCError | None = None

    @model_validator(mode="after")
    def validate_request_signature(self) -> Self:
        """Validate that at least ``original`` or ``error`` is set."""
        if self.original is None and self.error is None:
            raise ValueError("Either 'original' or 'error' must be provided")
        return self
