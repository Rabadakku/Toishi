"""Offline tripwire for the test run: any outbound connection from Python is an error.

Installed for the whole session by tests/conftest.py. Loopback (127.0.0.1, ::1,
localhost) and Unix sockets stay allowed, so local test servers work. The page's
own requests are checked separately in tests/ui (Playwright request routing).
"""

import ipaddress
import socket
from typing import Any


class OutboundNetworkError(RuntimeError):
    """Raised instead of opening a non-loopback connection."""


_REAL: dict[str, Any] = {
    "connect": socket.socket.connect,
    "connect_ex": socket.socket.connect_ex,
    "sendto": socket.socket.sendto,
}
_REAL_GETADDRINFO: Any = socket.getaddrinfo


def is_loopback(host: object) -> bool:
    if isinstance(host, bytes):
        host = host.decode()
    if host is None or host == "localhost":
        return True
    if not isinstance(host, str):
        return False
    try:
        return ipaddress.ip_address(host.split("%", 1)[0]).is_loopback
    except ValueError:
        return False


def _check(sock: socket.socket, address: Any) -> None:
    if sock.family == getattr(socket, "AF_UNIX", object()):
        return
    host = address[0] if isinstance(address, tuple) else address
    if not is_loopback(host):
        raise OutboundNetworkError(f"blocked outbound connection to {address!r}: tests run offline")


def _connect(self: socket.socket, address: Any) -> None:
    _check(self, address)
    _REAL["connect"](self, address)


def _connect_ex(self: socket.socket, address: Any) -> int:
    _check(self, address)
    result: int = _REAL["connect_ex"](self, address)
    return result


def _sendto(self: socket.socket, data: Any, *args: Any) -> int:
    _check(self, args[-1])
    result: int = _REAL["sendto"](self, data, *args)
    return result


def _getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
    if not is_loopback(host):
        raise OutboundNetworkError(f"blocked DNS lookup of {host!r}: tests run offline")
    return _REAL_GETADDRINFO(host, *args, **kwargs)


def install() -> None:
    patches: dict[str, Any] = {"connect": _connect, "connect_ex": _connect_ex, "sendto": _sendto}
    for name, replacement in patches.items():
        setattr(socket.socket, name, replacement)
    socket.getaddrinfo = _getaddrinfo


def uninstall() -> None:
    for name, original in _REAL.items():
        setattr(socket.socket, name, original)
    socket.getaddrinfo = _REAL_GETADDRINFO
