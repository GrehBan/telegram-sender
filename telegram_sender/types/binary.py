from typing import Protocol, runtime_checkable


@runtime_checkable
class BinaryReadable(Protocol):
    mode: str

    def read(self, n: int = -1, /) -> bytes: ...