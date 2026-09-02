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
RELEASE_VERSION = "4.2.2"
RELEASE_MESSAGE_ID = "release-4.2.2-2026-09"
EXPECTED_RELEASE_CONTENT = {
    "de": ("Medienstabilität", "Diagnose", "Protokollaufbewahrung"),
    "en": ("Media stability", "Diagnostics", "Log retention"),
    "es": ("Estabilidad multimedia", "Diagnóstico", "Conservación de registros"),
    "fr": ("Stabilité des médias", "Diagnostic", "Conservation des journaux"),
    "hu": ("Médiastabilitás", "Diagnosztika", "Naplók megőrzése"),
    "it": ("Stabilità dei media", "Diagnostica", "Conservazione dei log"),
    "ja": ("メディアの安定性", "診断", "ログの保存期間"),
    "nl": ("Mediastabiliteit", "Diagnostiek", "Logboeken bewaren"),
    "pl": ("Stabilność multimediów", "Diagnostyka", "Przechowywanie dzienników"),
    "pt_BR": ("Estabilidade da mídia", "Diagnóstico", "Retenção de logs"),
    "tl": ("Katatagan ng media", "Diagnostics", "Pagpapanatili ng mga log"),
}
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
        if f"jwtime-message-id: {RELEASE_MESSAGE_ID}" not in text:
            errors.append(
                f"{language}/communications.html: message id is not "
                f"{RELEASE_MESSAGE_ID}"
            )
        if RELEASE_VERSION not in text:
            errors.append(
                f"{language}/communications.html: visible release text omits {RELEASE_VERSION}"
            )

        index_path = ROOT / language / "index.html"
        if not index_path.exists():
            errors.append(f"{language}/index.html: page is missing")
        elif RELEASE_VERSION not in index_path.read_text(encoding="utf-8"):
            errors.append(
                f"{language}/index.html: release {RELEASE_VERSION} is missing"
            )

        media_label, diagnostics_label, retention_label = EXPECTED_RELEASE_CONTENT[
            language
        ]
        news_path = ROOT / language / "news.html"
        if not news_path.exists():
            errors.append(f"{language}/news.html: page is missing")
        else:
            news_text = news_path.read_text(encoding="utf-8")
            for fragment in (
                RELEASE_VERSION,
                "4.2.1",
                media_label,
                diagnostics_label,
            ):
                if fragment not in news_text:
                    errors.append(
                        f"{language}/news.html: expected content {fragment!r} is missing"
                    )

        manual_path = ROOT / language / "manual.html"
        if not manual_path.exists():
            errors.append(f"{language}/manual.html: page is missing")
        elif retention_label not in manual_path.read_text(encoding="utf-8"):
            errors.append(
                f"{language}/manual.html: log retention information is missing"
            )

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
