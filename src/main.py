from __future__ import annotations

import argparse
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    generator = EmailGenerator(faker_locale=args.locale, hops=args.hops)
    message = generator.create_message()

    writer = EmlWriter()
    output_path = writer.write(message, args.output)

    print(f"Wrote: {output_path.resolve()}")


if __name__ == "__main__":
    main()
