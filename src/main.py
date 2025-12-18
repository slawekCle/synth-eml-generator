from __future__ import annotations

import argparse
import json
from pathlib import Path

from generator import EmailGenerator, EmlWriter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a synthetic EML message")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("out") / "synthetic_test.eml",
        help="Ścieżka do wygenerowanego pliku .eml",
    )
    parser.add_argument(
        "--hops",
        type=int,
        default=3,
        help="Liczba nagłówków Received w łańcuchu",
    )
    parser.add_argument(
        "--locale",
        default="pl_PL",
        help="Locale używane przez bibliotekę Faker",
    )
    parser.add_argument(
        "-t",
        "--template",
        type=Path,
        required=True,
        help="Ścieżka do pliku szablonu wiadomości (JSON)",
    )
    return parser.parse_args()


def load_template(template_path: Path) -> tuple[str, str, str]:
    with template_path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Niepoprawny JSON: {exc}") from exc

    try:
        subject = data["subject"]
        text_body = data["text"]
        html_body = data["html"]
    except KeyError as exc:
        raise ValueError("Brak wymaganych kluczy: 'subject', 'text', 'html'") from exc

    if not all(isinstance(value, str) for value in (subject, text_body, html_body)):
        raise ValueError("Wartości 'subject', 'text' i 'html' muszą być typu string")

    return subject, text_body, html_body


def main() -> None:
    args = parse_args()

    if not args.template.is_file():
        raise SystemExit(f"Plik szablonu nie istnieje: {args.template}")

    try:
        template_subject, template_text, template_html = load_template(args.template)
    except ValueError as exc:
        raise SystemExit(f"Nie udało się wczytać szablonu: {exc}") from exc

    generator = EmailGenerator(faker_locale=args.locale, hops=args.hops)
    message = generator.create_message(
        subject=template_subject,
        text_body=template_text,
        html_body=template_html,
    )

    writer = EmlWriter()
    output_path = writer.write(message, args.output)

    print(f"Wrote: {output_path.resolve()}")


if __name__ == "__main__":
    main()
