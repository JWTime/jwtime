"""
Utility per costruire gli URL dei pacchetti pubblicati su GitHub.
"""

from typing import Literal

# Base pubblica su GitHub Pages dove vengono pubblicati i pacchetti
GITHUB_PACK_BASE = "https://jwtime.github.io/jwtime/packs"


def pack_lang_folder(lang_code: str) -> str:
    """
    Normalizza il codice lingua per la cartella/URL dei pack.
    """
    lc = (lang_code or "it").strip()
    return "pt_BR" if lc.lower() == "pt_br" else lc.lower()


def build_pack_url(lang_code: str, program_type: Literal["midweek", "weekend"], week_id: str) -> str:
    """
    Costruisce l'URL completo del file .jwtimepack su GitHub.
    """
    folder = pack_lang_folder(lang_code)
    return f"{GITHUB_PACK_BASE}/{folder}/{program_type}/{week_id}.jwtimepack"
