from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from email import policy
from email.generator import BytesGenerator
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from pathlib import Path

from faker import Faker


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


class EmailAddressGenerator:
    """Generate sender and recipient addresses."""

    def __init__(self, faker: Faker) -> None:
        self._faker = faker

    def sender(self) -> str:
        return self._build_address(domain=self._faker.domain_name())

    def recipient(self) -> str:
        return self._build_address(domain=self._faker.free_email_domain())

    def pair(self) -> tuple[str, str]:
        return self.sender(), self.recipient()

    def _build_address(self, *, domain: str) -> str:
        name = self._faker.name()
        local_part = self._faker.user_name()
        return f"{name} <{local_part}@{domain}>"


class EmlWriter:
    """Persist :class:`EmailMessage` objects as ``.eml`` files."""

    def __init__(self, *, max_header_len: int = 78) -> None:
        self.max_header_len = max_header_len

    def write(self, msg: EmailMessage, path: Path | str) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("wb") as f:
            generator = BytesGenerator(f, policy=policy.SMTP, maxheaderlen=self.max_header_len)
            generator.flatten(msg)

        return output_path


class EmailGenerator:
    """High-level orchestrator for synthetic EML generation."""

    def __init__(
        self,
        *,
        faker_locale: str = "pl_PL",
        helo: str = "smtp-client.example.net",
        hops: int = 3,
    ) -> None:
        self.faker = Faker(faker_locale)
        self.received_builder = ReceivedChainBuilder(helo=helo, hops=hops)
        self.address_generator = EmailAddressGenerator(self.faker)

    def create_message(
        self,
        *,
        from_addr: str | None = None,
        to_addr: str | None = None,
        subject: str,
        text_body: str,
        html_body: str,
        hops: int | None = None,
    ) -> EmailMessage:
        sender, recipient = self._resolve_addresses(from_addr, to_addr)
        self._validate_content(subject, text_body, html_body)

        msg = EmailMessage(policy=policy.SMTP)
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg["Date"] = format_datetime(datetime.now(timezone.utc))
        msg["Message-ID"] = make_msgid(domain="example.net")
        msg["MIME-Version"] = "1.0"

        for received_value in self.received_builder.build(recipient=recipient, hops=hops):
            msg["Received"] = received_value

        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        return msg

    def _resolve_addresses(self, from_addr: str | None, to_addr: str | None) -> tuple[str, str]:
        sender = from_addr or self.address_generator.sender()
        recipient = to_addr or self.address_generator.recipient()
        return sender, recipient

    def _validate_content(self, subject: str, text_body: str, html_body: str) -> None:
        if not all(isinstance(value, str) for value in (subject, text_body, html_body)):
            raise TypeError("Treść wiadomości musi być typu string")
