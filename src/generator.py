from __future__ import annotations

from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid, parseaddr

from faker import Faker

from core.received_chain_builder import ReceivedChainBuilder
from email_address_generator import EmailAddressGenerator


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
        msg["Return-Path"] = f"<{self._extract_email_address(sender)}>"
        msg["Reply-To"] = sender
        msg["Subject"] = subject
        msg["Date"] = format_datetime(datetime.now(timezone.utc))
        message_id_domain = (
            ReceivedChainBuilder._extract_domain(sender)
            or ReceivedChainBuilder._domain_from_hostname(self.received_builder.default_helo)
            or "example.net"
        )
        msg["Message-ID"] = make_msgid(domain=message_id_domain)
        msg["MIME-Version"] = "1.0"
        msg["X-Mailer"] = "synth-eml-generator"

        for received_value in self.received_builder.build(sender=sender, recipient=recipient, hops=hops):
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

    @staticmethod
    def _extract_email_address(address: str) -> str:
        _, email_addr = parseaddr(address)
        return email_addr or address
