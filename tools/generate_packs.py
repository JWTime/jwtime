"""
Script batch per generare i pacchetti .jwtimepack (12 settimane) e pubblicarli sotto packs/.
"""

import asyncio
import logging
import sys
import contextlib
from pathlib import Path
from typing import List

from data_extraction import base as base_lang
from data_extraction.midweek import MidweekDataExtraction
from data_extraction.weekend import WeekendDataExtraction
from backup.backup_manager import BackupPackage, get_iso_week_id
from backup.pack_manager import PackManager
from utils.github_packs import pack_lang_folder

# Cartella radice del sito (per Pages diretto in root)
BASE_DIR = Path(__file__).resolve().parent.parent
SITE_ROOT = BASE_DIR
PACKS_ROOT = SITE_ROOT / "packs"

# Lingue supportate (riusiamo la mappa centrale)
SUPPORTED_LANGS: List[str] = list(base_lang._LANG.keys())  # type: ignore[attr-defined]


def _ensure_site_root():
    # La root del repo deve esistere; crea la cartella packs se manca
    if not SITE_ROOT.exists():
        raise RuntimeError(f"Site root non trovata: {SITE_ROOT}")
    PACKS_ROOT.mkdir(parents=True, exist_ok=True)


async def _generate_for_week(lang: str, week_offset: int, week_id: str):
    """
    Genera i due pacchetti (midweek/weekend) per una lingua e settimana.
    """
    logging.info("=== %s week %s (offset=%s) ===", lang, week_id, week_offset)

    # Estrazione midweek
    mid_extractor = MidweekDataExtraction(settimana_offset=week_offset, lang_code=lang)
    rows_mid = await mid_extractor.estrai_dati()
    if rows_mid:
        await _export_package(lang, "midweek", week_id, rows_mid)
    else:
        logging.warning("[midweek] Nessun dato per %s %s", lang, week_id)

    # Estrazione weekend
    wk_extractor = WeekendDataExtraction(settimana_offset=week_offset, lang_code=lang)
    rows_wk = await wk_extractor.estrai_dati()
    if rows_wk:
        await _export_package(lang, "weekend", week_id, rows_wk)
    else:
        logging.warning("[weekend] Nessun dato per %s %s", lang, week_id)


async def _export_package(lang: str, program_type: str, week_id: str, rows):
    """
    Crea il BackupPackage e lo esporta in formato .jwtimepack nella struttura website/packs.
    """
    package = BackupPackage(
        program_type=program_type,
        week_id=week_id,
        rows=rows,
        ui_lang=lang,
        page_lang=lang
    )

    lang_folder = pack_lang_folder(lang)
    out_dir = PACKS_ROOT / lang_folder / program_type
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{week_id}.jwtimepack"

    # Log sintetico per tracciare cosa stiamo salvando
    logging.info("Scrivo %s", out_file)
    success = PackManager.export_packages([package], str(out_file))
    if not success:
        logging.error("Errore export pack: %s", out_file)


def _clean_old_packs(valid_week_ids: List[str]):
    """
    Rimuove i pacchetti che non rientrano nella finestra delle 12 settimane correnti.
    """
    valid_set = set(valid_week_ids)

    for lang in SUPPORTED_LANGS:
        lang_folder = pack_lang_folder(lang)
        for program_type in ("midweek", "weekend"):
            dir_path = PACKS_ROOT / lang_folder / program_type
            if not dir_path.exists():
                continue
            for file_path in dir_path.glob("*.jwtimepack"):
                week_id = file_path.stem
                if week_id not in valid_set:
                    logging.info("Pulizia: elimino pack vecchio %s", file_path)
                    with contextlib.suppress(Exception):
                        file_path.unlink()


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    _ensure_site_root()

    # Calcola le 12 settimane (corrente + 11 successive)
    week_ids = [get_iso_week_id(offset) for offset in range(12)]

    # Genera i pacchetti per tutte le lingue supportate
    for lang in SUPPORTED_LANGS:
        for offset, week_id in enumerate(week_ids):
            await _generate_for_week(lang, offset, week_id)

    # Pulizia dei file fuori finestra
    _clean_old_packs(week_ids)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        logging.error("Errore durante la generazione dei pacchetti: %s", exc)
        sys.exit(1)
