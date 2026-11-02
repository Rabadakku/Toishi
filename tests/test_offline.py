import socket
import threading

import pytest

from tests.offline import OutboundNetworkError, is_loopback

TEST_NET = ("203.0.113.7", 80)  # RFC 5737 documentation range: never routed


def test_outbound_connect_is_blocked() -> None:
    with socket.socket() as sock, pytest.raises(OutboundNetworkError):
        sock.connect(TEST_NET)


def test_outbound_connect_ex_and_create_connection_are_blocked() -> None:
    with socket.socket() as sock, pytest.raises(OutboundNetworkError):
        sock.connect_ex(TEST_NET)
    with pytest.raises(OutboundNetworkError):
        socket.create_connection(TEST_NET, timeout=1)


def test_dns_lookup_of_remote_name_is_blocked() -> None:
    with pytest.raises(OutboundNetworkError):
        socket.getaddrinfo("example.com", 443)


def test_udp_sendto_remote_is_blocked() -> None:
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with udp, pytest.raises(OutboundNetworkError):
        udp.sendto(b"x", ("203.0.113.7", 53))


def test_loopback_still_works() -> None:
    with socket.create_server(("127.0.0.1", 0)) as server:
        port = server.getsockname()[1]
        accepted = threading.Thread(target=lambda: server.accept()[0].close())
        accepted.start()
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            pass
        accepted.join(timeout=2)


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("127.0.0.1", True),
        ("::1", True),
        ("localhost", True),
        (None, True),
        ("10.0.0.1", False),
        ("example.com", False),
        ("", False),
    ],
)
def test_is_loopback(host: object, expected: bool) -> None:
    assert is_loopback(host) is expected
