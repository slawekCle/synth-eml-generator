from __future__ import annotations

from faker import Faker


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
