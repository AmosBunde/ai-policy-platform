"""SSRF prevention: reject private/internal IP ranges and non-HTTP schemes."""
import ipaddress
import re
import socket
from urllib.parse import urlparse


_BLOCKED_SCHEMES = {"file", "ftp", "gopher", "data", "javascript"}

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def validate_url(url: str) -> str:
    """Validate a URL is safe to fetch (no SSRF).

    Raises ValueError if the URL targets private networks or uses blocked schemes.
    """
    parsed = urlparse(url)

    if not parsed.scheme or not parsed.hostname:
        raise ValueError(f"Invalid URL: {url}")

    if parsed.scheme.lower() in _BLOCKED_SCHEMES:
        raise ValueError(f"Blocked URL scheme: {parsed.scheme}")

    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError(f"Only HTTP/HTTPS URLs allowed, got: {parsed.scheme}")

    hostname = parsed.hostname

    # Check for IP address directly
    try:
        ip = ipaddress.ip_address(hostname)
        for network in _PRIVATE_NETWORKS:
            if ip in network:
                raise ValueError(f"URL resolves to private IP range: {hostname}")
        return url
    except ValueError as e:
        if "private IP" in str(e):
            raise
        # Not an IP, it's a hostname — resolve it
        pass

    # Resolve hostname to check for DNS rebinding to private IPs
    try:
        addrs = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for family, _, _, _, sockaddr in addrs:
            ip = ipaddress.ip_address(sockaddr[0])
            for network in _PRIVATE_NETWORKS:
                if ip in network:
                    raise ValueError(
                        f"URL hostname {hostname} resolves to private IP: {sockaddr[0]}"
                    )
    except socket.gaierror:
        # Can't resolve — allow it (will fail at fetch time)
        pass

    return url
