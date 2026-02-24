from enum import StrEnum


class OS(StrEnum):
    """Supported operating systems for device profile generation."""

    WINDOWS = "Windows"
    MACOS = "macOS"
    LINUX = "Linux"
    ANDROID = "Android"
