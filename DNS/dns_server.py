#!/usr/bin/env python3
"""
Threaded DNS proxy that blocks domains based on should_block() from inference.py.

Features:
- Parses incoming DNS queries on UDP/53
- Consults cached should_block decision
- Returns NXDOMAIN for blocked domains (sinkhole example included as comment)
- Forwards allowed queries to Google DNS (8.8.8.8) and relays responses
- Caches successful responses to reduce upstream load
"""

from __future__ import annotations

import logging
import socket
import socketserver
import threading
import time
from typing import Dict, Optional, Tuple

from dnslib import A, DNSLabel, DNSRecord, QTYPE, RCODE, RR

try:
    from .inference import should_block  # Import existing API
except ImportError:  # pragma: no cover - standalone fallback
    from inference import should_block

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 53
UPSTREAM_SERVER = ("8.8.8.8", 53)
SOCKET_TIMEOUT = 5.0

BLOCK_CACHE_TTL = 300  # seconds
RESPONSE_CACHE_TTL = 60


# ---------------------------------------------------------------------------
# Simple TTL Cache
# ---------------------------------------------------------------------------


class TTLCache:
    """Thread-safe TTL cache used for block decisions and DNS responses."""

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[float, object]] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            expires_at, value = item
            if expires_at < time.time():
                del self._store[key]
                return None
            return value

    def set(self, key: str, value, ttl: float) -> None:
        with self._lock:
            self._store[key] = (time.time() + ttl, value)


block_cache = TTLCache()
response_cache = TTLCache()


# ---------------------------------------------------------------------------
# DNS Server Implementation
# ---------------------------------------------------------------------------


class ThreadedDNSServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    """Threaded UDP server that listens for DNS packets."""

    allow_reuse_address = True


class DNSHandler(socketserver.BaseRequestHandler):
    """Process incoming DNS queries."""

    def handle(self) -> None:
        data, sock = self.request
        try:
            dns_request = DNSRecord.parse(data)
        except Exception as exc:  # pragma: no cover - defensive
            logging.error("Failed to parse DNS packet: %s", exc)
            return

        qname = str(dns_request.q.qname).rstrip(".")
        qtype = QTYPE.get(dns_request.q.qtype, "UNKNOWN")
        cache_key = f"{qname}:{qtype}"

        # Serve cached upstream response if present
        cached_response = response_cache.get(cache_key)
        if cached_response:
            sock.sendto(cached_response, self.client_address)
            logging.info("[CACHE] %s (%s)", qname, qtype)
            return

        # Determine block decision (cached)
        block_decision = block_cache.get(qname)
        if block_decision is None:
            try:
                block_decision = bool(should_block(qname))
            except Exception as exc:  # pragma: no cover - inference error
                logging.error("should_block failed for %s: %s", qname, exc)
                block_decision = False
            block_cache.set(qname, block_decision, BLOCK_CACHE_TTL)

        if block_decision:
            response = self._build_nxdomain(dns_request)
            # Optional sinkhole example:
            # response = self._build_sinkhole(dns_request, "0.0.0.0")
            sock.sendto(response.pack(), self.client_address)
            logging.info("[BLOCK] %s", qname)
            return

        # Forward to upstream resolver
        upstream = self._forward_to_upstream(data)
        if upstream:
            sock.sendto(upstream, self.client_address)
            response_cache.set(cache_key, upstream, RESPONSE_CACHE_TTL)
            logging.info("[ALLOW] %s", qname)
        else:
            servfail = self._build_servfail(dns_request)
            sock.sendto(servfail.pack(), self.client_address)
            logging.error("[ERROR] Upstream resolution failed for %s", qname)

    @staticmethod
    def _forward_to_upstream(payload: bytes) -> Optional[bytes]:
        """Send query to the real resolver and return bytes response."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as upstream_sock:
            upstream_sock.settimeout(SOCKET_TIMEOUT)
            try:
                upstream_sock.sendto(payload, UPSTREAM_SERVER)
                response, _ = upstream_sock.recvfrom(4096)
                return response
            except socket.timeout:
                logging.error("Upstream timeout to %s", UPSTREAM_SERVER)
            except OSError as exc:
                logging.error("Upstream socket error: %s", exc)
        return None

    @staticmethod
    def _build_nxdomain(request: DNSRecord) -> DNSRecord:
        """Craft NXDOMAIN response mirroring original question."""
        reply = request.reply()
        reply.header.rcode = RCODE.NXDOMAIN
        return reply

    @staticmethod
    def _build_sinkhole(request: DNSRecord, ip_addr: str) -> DNSRecord:
        """Return response pointing to sinkhole IP (disabled by default)."""
        reply = request.reply()
        reply.add_answer(RR(rname=request.q.qname, rtype=QTYPE.A, rdata=A(ip_addr), ttl=60))
        return reply

    @staticmethod
    def _build_servfail(request: DNSRecord) -> DNSRecord:
        """Return SERVFAIL packet when upstream resolver fails."""
        reply = request.reply()
        reply.header.rcode = RCODE.SERVFAIL
        return reply


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logging.info("Starting DNS proxy on %s:%d (forwarding to %s:%d)", LISTEN_HOST, LISTEN_PORT, *UPSTREAM_SERVER)

    with ThreadedDNSServer((LISTEN_HOST, LISTEN_PORT), DNSHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logging.info("DNS proxy shutting down")
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
