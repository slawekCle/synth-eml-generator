from __future__ import annotations

from datetime import datetime, timezone
from email import policy
from email.generator import BytesGenerator
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from pathlib import Path

from faker import Faker

from received_chain_builder import ReceivedChainBuilder


class EmailContentGenerator:
    """Generate the subject and bodies of an email."""

    def __init__(self, faker: Faker) -> None:
        self._faker = faker

    def generate(self) -> tuple[str, str, str]:
        subject = f"{self._faker.catch_phrase()} – {self._faker.bs()}"
        paragraphs = self._faker.paragraphs(nb=3)

        text_body = "\n\n".join(["Cześć,"] + paragraphs + [self._closing_signature()])
        html_body = "".join(
            [
                "<html><body>",
                "<p>Cześć,</p>",
                *(f"<p>{paragraph}</p>" for paragraph in paragraphs),
                f"<p>{self._closing_signature(html=True)}</p>",
                "</body></html>",
            ]
        )

        return subject, text_body, html_body

    def _closing_signature(self, *, html: bool = False) -> str:
        closing = ["Pozdrawiam,", self._faker.company()]
        if html:
            return "<br/>".join(closing)
        return "\n".join(closing)


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
        self.content_generator = EmailContentGenerator(self.faker)

    def create_message(
        self,
        *,
        from_addr: str | None = None,
        to_addr: str | None = None,
        subject: str | None = None,
        text_body: str | None = None,
        html_body: str | None = None,
        hops: int | None = None,
    ) -> EmailMessage:
        sender, recipient = self._resolve_addresses(from_addr, to_addr)
        subject, text_body, html_body = self._resolve_content(subject, text_body, html_body)

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

    def _resolve_content(
        self, subject: str | None, text_body: str | None, html_body: str | None
    ) -> tuple[str, str, str]:
        if subject is None or text_body is None or html_body is None:
            generated_subject, generated_text, generated_html = self.content_generator.generate()
            subject = subject or generated_subject
            text_body = text_body or generated_text
            html_body = html_body or generated_html

        return subject, text_body, html_body
