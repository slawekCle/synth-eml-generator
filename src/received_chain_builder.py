from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime


class ReceivedChainBuilder:
    """Build a plausible chain of ``Received`` headers."""

    def __init__(
        self,
        *,
        helo: str = "smtp-client.example.net",
        hops: int = 3,
    ) -> None:
        self.helo = helo
        self.hops = hops

    def build(
        self,
        recipient: str,
        *,
        start_time: datetime | None = None,
        hops: int | None = None,
    ) -> list[str]:
        """
        Generate a plausible chain of Received headers.

        Newest headers are placed first to mimic a real SMTP chain.
        """

        effective_start = start_time or datetime.now(timezone.utc)
        hop_count = hops if hops is not None else self.hops

        doc_ipv4 = ["192.0.2.10", "198.51.100.23", "203.0.113.77"]
        doc_hosts = ["mx1.example.net", "mx2.example.net", "edge.example.net", "mailhub.example.net"]

        timestamp = effective_start - timedelta(minutes=2 * hop_count)
        received_values: list[str] = []

        for i in range(hop_count):
            timestamp += timedelta(minutes=2)
            ip = doc_ipv4[i % len(doc_ipv4)]
            by_host = doc_hosts[i % len(doc_hosts)]
            frm_host = doc_hosts[(i + 1) % len(doc_hosts)]
            esmtp_id = secrets.token_hex(6)

            value = (
                f"from {self.helo} ({frm_host} [{ip}])"
                f"\tby {by_host} with ESMTP id {esmtp_id}"
                f"\tfor <{recipient}>;"
                f"\t{format_datetime(timestamp)}"
            )
            received_values.append(value)

        return list(reversed(received_values))
