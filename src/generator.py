from __future__ import annotations

from email.message import EmailMessage
from email.generator import BytesGenerator
from email import policy
from email.utils import format_datetime, make_msgid
from pathlib import Path
from datetime import datetime, timezone, timedelta
import secrets


def build_received_chain(
    helo: str,
    recipient: str,
    hops: int = 3,
    start_time: datetime | None = None,
) -> list[str]:
    """
    Generate a plausible chain of Received: headers.
    Note: In real life, each hop adds its own Received. Here we simulate it.
    Uses documentation IP ranges (RFC 5737 / RFC 3849).
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc)

    doc_ipv4 = ["192.0.2.10", "198.51.100.23", "203.0.113.77"]
    doc_hosts = ["mx1.example.net", "mx2.example.net", "edge.example.net", "mailhub.example.net"]

    # We'll build older -> newer timestamps, but headers must be inserted newest first.
    t = start_time - timedelta(minutes=2 * hops)
    received_values: list[str] = []

    for i in range(hops):
        t = t + timedelta(minutes=2)  # monotonic time
        ip = doc_ipv4[i % len(doc_ipv4)]
        by_host = doc_hosts[i % len(doc_hosts)]
        frm_host = doc_hosts[(i + 1) % len(doc_hosts)]
        esmtp_id = secrets.token_hex(6)

        # A single Received header value (no "Received:" prefix here).
        # We include line breaks + indentation for proper folding.
        value = (
            f"from {helo} ({frm_host} [{ip}])"
            f"\tby {by_host} with ESMTP id {esmtp_id}"
            f"\tfor <{recipient}>;"
            f"\t{format_datetime(t)}"
        )
        received_values.append(value)

    # Newest should appear at the top of the message => reverse
    return list(reversed(received_values))


def make_eml(
    from_addr: str,
    to_addr: str,
    subject: str,
    text_body: str,
    html_body: str,
    hops: int = 3,
) -> EmailMessage:
    msg = EmailMessage(policy=policy.SMTP)

    # Core headers
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Date"] = format_datetime(datetime.now(timezone.utc))
    msg["Message-ID"] = make_msgid(domain="example.net")
    msg["MIME-Version"] = "1.0"

    # Simulated "Received" chain (newest first)
    for rcv in build_received_chain(helo="smtp-client.example.net", recipient=to_addr, hops=hops):
        # print(type(rcv))
        # msg.add_header("Received", rcv, charset="utf-8")
        msg["Received"] = rcv

    # Body as multipart/alternative
    msg.set_content(text_body)  # text/plain
    msg.add_alternative(html_body, subtype="html")  # text/html

    return msg


def write_eml(msg: EmailMessage, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        gen = BytesGenerator(f, policy=policy.SMTP, maxheaderlen=78)
        gen.flatten(msg)


if __name__ == "__main__":
    eml = make_eml(
        from_addr="Test Sender <sender@example.net>",
        to_addr="recipient@example.com",
        subject="Testowa wiadomość (bezpieczna) – powiadomienie",
        text_body=(
            "Cześć,\n\n"
            "To jest bezpieczna, syntetyczna wiadomość do testów filtrów.\n"
            "Nie zawiera linków ani złośliwych załączników.\n\n"
            "Pozdrawiam,\nZespół Testów\n"
        ),
        html_body=(
            "<html><body>"
            "<p>Cześć,</p>"
            "<p>To jest <b>bezpieczna</b>, syntetyczna wiadomość do testów filtrów.</p>"
            "<p>Nie zawiera linków ani złośliwych załączników.</p>"
            "<p>Pozdrawiam,<br/>Zespół Testów</p>"
            "</body></html>"
        ),
        hops=4,
    )

    out = Path("out") / "synthetic_test.eml"
    write_eml(eml, out)
    print(f"Wrote: {out.resolve()}")