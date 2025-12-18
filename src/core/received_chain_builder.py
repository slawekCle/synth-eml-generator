from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime, parseaddr
from ipaddress import IPv4Address


class ReceivedChainBuilder:
    """Build a plausible chain of ``Received`` headers."""

    def __init__(
        self,
        *,
        helo: str = "smtp-client.example.net",
        hops: int = 3,
    ) -> None:
        self.default_helo = helo
        self.hops = hops

    def build(
        self,
        sender: str,
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

        sender_domain = self._extract_domain(sender) or self._domain_from_hostname(self.default_helo) or "example.net"
        recipient_domain = self._extract_domain(recipient) or sender_domain
        host_chain = self._build_host_chain(sender_domain, recipient_domain, hop_count)
        ip_chain = self._generate_public_ips(hop_count)

        timestamp = effective_start - timedelta(minutes=2 * hop_count)
        received_values: list[str] = []

        for i in range(hop_count):
            timestamp += timedelta(minutes=2)
            from_host = host_chain[i]
            by_host = host_chain[i + 1]
            helo_value = from_host or self.default_helo
            ip = ip_chain[i]
            esmtp_id = secrets.token_hex(6)

            value = (
                f"from {helo_value} ({from_host} [{ip}])"
                f"\tby {by_host} with ESMTP id {esmtp_id}"
                f"\tfor <{recipient}>;"
                f"\t{format_datetime(timestamp)}"
            )
            received_values.append(value)

        return list(reversed(received_values))

    @staticmethod
    def _extract_domain(address: str) -> str | None:
        _, email_addr = parseaddr(address)
        if "@" not in email_addr:
            return None
        domain = email_addr.split("@", 1)[1].strip()
        return domain.lower() if domain else None

    @staticmethod
    def _domain_from_hostname(hostname: str) -> str | None:
        parts = hostname.split(".")
        if len(parts) < 2:
            return None
        return ".".join(parts[-2:])

    def _build_host_chain(self, sender_domain: str, recipient_domain: str, hop_count: int) -> list[str]:
        total_hosts = max(2, hop_count + 1)
        host_chain: list[str] = []

        for idx in range(total_hosts):
            if idx == total_hosts - 1:
                host_chain.append(f"mail.{recipient_domain}")
            elif idx >= max(1, total_hosts // 2):
                host_chain.append(f"mx{idx - (total_hosts // 2) + 1}.{recipient_domain}")
            else:
                host_chain.append(f"smtp{idx + 1}.{sender_domain}")

        return host_chain

    def _generate_public_ips(self, count: int) -> list[str]:
        ips: list[str] = []
        seen: set[str] = set()

        while len(ips) < count:
            candidate = IPv4Address(secrets.randbits(32))
            if not candidate.is_global:
                continue

            as_text = str(candidate)
            if as_text in seen:
                continue

            ips.append(as_text)
            seen.add(as_text)

        return ips
