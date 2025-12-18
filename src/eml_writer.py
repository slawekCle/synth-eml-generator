from __future__ import annotations

from email import policy
from email.generator import BytesGenerator
from email.message import EmailMessage
from pathlib import Path


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
