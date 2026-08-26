"""Validate the language-specific metadata consumed by JW Time."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_LANGUAGES = {
    "de",
    "en",
    "es",
    "fr",
    "hu",
    "it",
    "ja",
    "nl",
    "pl",
    "pt_BR",
    "tl",
}
RELEASE_VERSION = "4.2.1"
COLOR_DIRECTIVE_RE = re.compile(r"\[([^\]=\s]+)\s*=\s*#[0-9A-Fa-f]{6}\]")


def main() -> int:
    errors: list[str] = []
    pages = {
        path.parent.name: path
        for path in ROOT.glob("*/communications.html")
        if path.parent.is_dir()
    }

    missing = EXPECTED_LANGUAGES - pages.keys()
    unexpected = pages.keys() - EXPECTED_LANGUAGES
    if missing:
        errors.append(f"missing communications pages: {', '.join(sorted(missing))}")
    if unexpected:
        errors.append(f"unexpected communications pages: {', '.join(sorted(unexpected))}")

    for language in sorted(EXPECTED_LANGUAGES & pages.keys()):
        text = pages[language].read_text(encoding="utf-8")
        directives = COLOR_DIRECTIVE_RE.findall(text)
        if directives != ["color"]:
            errors.append(
                f"{language}/communications.html: expected exactly [color=#RRGGBB], "
                f"found commands {directives!r}"
            )
        if f"jwtime-target-version: {RELEASE_VERSION}" not in text:
            errors.append(
                f"{language}/communications.html: target version is not {RELEASE_VERSION}"
            )
        if RELEASE_VERSION not in text:
            errors.append(
                f"{language}/communications.html: visible release text omits {RELEASE_VERSION}"
            )

        news_path = ROOT / language / "news.html"
        if not news_path.exists():
            errors.append(f"{language}/news.html: page is missing")
        elif RELEASE_VERSION not in news_path.read_text(encoding="utf-8"):
            errors.append(f"{language}/news.html: release {RELEASE_VERSION} is missing")

    if errors:
        print("Site release audit: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Site release audit: OK ({len(EXPECTED_LANGUAGES)} languages, "
        f"release {RELEASE_VERSION})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
