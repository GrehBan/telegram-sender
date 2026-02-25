"""Resolve typed proxy objects into Pyrogram-compatible dicts.

Pyrogram expects::

    dict(scheme="socks5", hostname="11.22.33.44", port=1234,
         username="user", password="pass")

This module maps :class:`MTProtoProxy`, :class:`SocksProxy`,
and :class:`HTTPSProxy` TypedDicts into that format, both
individually and in bulk via :func:`resolve_proxies`.
"""

from collections.abc import Sequence
from random import Random
from typing import Any, Literal, NotRequired, TypeAlias, TypedDict


class MTProtoProxy(TypedDict):
    """MTProto proxy configuration.

    Attributes:
        scheme: Must be ``"mtproto"``.
        server: Proxy server address.
        port: Proxy server port.
        secret: MTProto secret key.
    """

    scheme: Literal["mtproto"]
    server: str
    port: int
    secret: str


class SocksProxy(TypedDict):
    """SOCKS5 proxy configuration.

    Attributes:
        scheme: Must be ``"socks5"``.
        host: Proxy server address.
        port: Proxy server port.
        username: Optional authentication username.
        password: Optional authentication password.
    """

    scheme: Literal["socks5"]
    host: str
    port: int
    username: NotRequired[str]
    password: NotRequired[str]


class HTTPSProxy(TypedDict):
    """HTTPS proxy configuration.

    Attributes:
        scheme: Must be ``"https"``.
        host: Proxy server address.
        port: Proxy server port.
        username: Optional authentication username.
        password: Optional authentication password.
    """

    scheme: Literal["https"]
    host: str
    port: int
    username: NotRequired[str]
    password: NotRequired[str]


Proxy: TypeAlias = MTProtoProxy | SocksProxy | HTTPSProxy  # noqa: UP040
ProxySeq: TypeAlias = Sequence[Proxy]  # noqa: UP040


def resolve_proxies(
    proxies: ProxySeq,
) -> Sequence[dict[str, Any]]:
    """Resolve a sequence of typed proxy dicts into
    Pyrogram's format.

    Delegates each item to :func:`resolve_proxy`.

    Args:
        proxies: A sequence of ``Proxy`` dicts.

    Returns:
        A sequence of Pyrogram-compatible proxy dicts.
    """
    resolved = []
    for proxy in proxies:
        resolved.append(resolve_proxy(proxy))
    return resolved


def resolve_proxy(proxy: Proxy) -> dict[str, Any]:
    """Resolve a single typed proxy dict into Pyrogram's
    format.

    Args:
        proxy: One of ``MTProtoProxy``, ``SocksProxy``, or
            ``HTTPSProxy``.

    Returns:
        A dict with ``scheme``, ``hostname``, ``port``, and
        optionally ``username`` / ``password`` / ``secret``.

    Raises:
        ValueError: If the scheme is unrecognised.
    """
    scheme = proxy["scheme"]

    if scheme == "mtproto":
        return {
            "scheme": scheme,
            "hostname": proxy["server"],  # type: ignore[typeddict-item]
            "port": proxy["port"],
            "secret": proxy["secret"],  # type: ignore[typeddict-item]
        }

    if scheme in {"socks5", "https"}:
        result: dict[str, Any] = {
            "scheme": scheme,
            "hostname": proxy["host"],  # type: ignore[typeddict-item]
            "port": proxy["port"],
        }
        if "username" in proxy:
            result["username"] = proxy["username"]  # type: ignore[typeddict-item]
        if "password" in proxy:
            result["password"] = proxy["password"]  # type: ignore[typeddict-item]
        return result

    raise ValueError(f"Unrecognised proxy scheme: {scheme!r}")


def pick_random_proxy(
    proxies: ProxySeq,
    seed: str | int | None,
) -> dict[str, Any]:
    """Pick and resolve a single proxy deterministically.

    Uses the *seed* to select a proxy from *proxies* so that
    the same seed always yields the same choice.  Intended to
    pair with a session name, mirroring the device-profile
    seeding pattern in ``MessageSender``.

    Args:
        proxies: A non-empty sequence of ``Proxy`` dicts.
        seed: Deterministic seed (typically the session name).

    Returns:
        A Pyrogram-compatible proxy dict.

    Raises:
        ValueError: If *proxies* is empty.
    """
    if not proxies:
        raise ValueError("Proxy sequence is empty")

    idx = Random(seed).randrange(len(proxies))
    return resolve_proxy(proxies[idx])
