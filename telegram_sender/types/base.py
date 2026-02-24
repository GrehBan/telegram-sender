from pydantic import BaseModel, ConfigDict


class BaseType(BaseModel):
    """Base immutable Pydantic model for all domain types."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        use_enum_values=True,
        arbitrary_types_allowed=True
    )
