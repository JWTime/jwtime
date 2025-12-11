import re
import aiohttp
import asyncio
import logging
import tempfile
import contextlib
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from PyQt5.QtCore import QCoreApplication

from data_extraction.base import (
    DataExtractionBase,
    get_language_strings,
    normalize_lang_code,
    get_route_info,
    find_meeting_link,
    detect_page_lang_from_soup,
    ensure_url_language,
)
from backup.pack_manager import PackManager
from utils.github_packs import build_pack_url

def build_accept_language(lang_code: str) -> str:
    # Special handling for pt_BR before normalization
    lang_lower = (lang_code or "").lower().strip()
    if lang_lower == "pt_br":
        return "pt-BR,pt;q=0.9,en;q=0.8"

    lc = normalize_lang_code(lang_code)
    mapping = {
        "it": "it-IT,it;q=0.9,en;q=0.8",
        "en": "en-US,en;q=0.9",
        "fr": "fr-FR,fr;q=0.9,en;q=0.8",
        "es": "es-ES,es;q=0.9,en;q=0.8",
        "de": "de-DE,de;q=0.9,en;q=0.8",
        "pt": "pt-BR,pt;q=0.9,en;q=0.8",
    }
    return mapping.get(lc, "it-IT,it;q=0.9,en;q=0.8")

def clock(mm: int) -> str:
    try:
        m = int(mm)
    except Exception:
        m = 0
    return f"{m:01d}:00"


class WeekendDataExtraction(DataExtractionBase):
    def __init__(self, settimana_offset: int = 0, lang_code: str = "it", progress_callback=None):
        # Store the original language code (e.g., pt_BR)
        self.original_lang_code = (lang_code or "it").lower().strip()

        # For URL construction, convert pt_BR to pt
        if self.original_lang_code == "pt_br":
            self.request_lang = "pt"
        else:
            self.request_lang = normalize_lang_code(lang_code or "it")

        self.settimana_offset = settimana_offset or 0
        # Use original code for getting language strings (pt_BR)
        self.lang_code = self.original_lang_code
        self.lang = get_language_strings(self.lang_code)
        self.progress_callback = progress_callback

    async def estrai_dati(self):
        try:
            anchor = datetime.now() + timedelta(weeks=self.settimana_offset)
            year, week = anchor.isocalendar()[0], anchor.isocalendar()[1]
            week_id = f"{year:04d}-{week:02d}"
            # Use original_lang_code (pt_BR) to get route info, use request_lang (pt) for URL
            r_code, lp_code = get_route_info(self.original_lang_code)
            meetings_url = f"https://wol.jw.org/{self.request_lang}/wol/meetings/{r_code}/{lp_code}/{year}/{week}"

            headers = {
                "Accept-Language": build_accept_language(self.original_lang_code),
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JWTime/1.0",
            }

            if self.progress_callback:
                await self.progress_callback(5, QCoreApplication.translate("WeekendDataExtraction", "Apro la pagina della settimana…"))

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(meetings_url) as resp:
                    resp.raise_for_status()
                    html = await resp.text()

                soup = BeautifulSoup(html, "html.parser")
                # Use original_lang_code (pt_BR) to search for labels, not request_lang (pt)
                wt_url = find_meeting_link(soup, meetings_url, self.original_lang_code, kind="watchtower")
                if not wt_url:
                    logging.warning("[Weekend] Link Watchtower non trovato per la lingua %s", self.request_lang)
                    if self.progress_callback:
                        await self.progress_callback(100, "[Weekend] Link Watchtower non trovato per la lingua " + self.request_lang.upper())
                    return []

                wt_url = ensure_url_language(wt_url, self.request_lang, (r_code, lp_code))

                if self.progress_callback:
                    await self.progress_callback(20, QCoreApplication.translate("WeekendDataExtraction", "Apro la pagina della Torre di Guardia…"))

                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(wt_url) as resp:
                        resp.raise_for_status()
                        wt_html = await resp.text()

                soup_wt = BeautifulSoup(wt_html, "html.parser")

            # Manteniamo sempre la lingua richiesta per i testi dell'interfaccia
            detected = detect_page_lang_from_soup(soup_wt)
            if detected and detected != self.request_lang:
                logging.warning("[Weekend] Page language is %s but requested %s. This may cause extraction issues.", detected, self.request_lang)
            # NON cambiamo self.lang_code - manteniamo la lingua richiesta

            c_label = self.lang.get("CANTICO", "Cantico")
            rx_song = re.compile(rf"{re.escape(c_label)}\s+(\d+)", re.IGNORECASE)
            text = soup_wt.get_text(" ", strip=True)
            songs = []
            for m in rx_song.finditer(text):
                n = m.group(1)
                if n not in songs:
                    songs.append(n)
                if len(songs) >= 2:
                    break

            title = self._article_title(soup_wt) or QCoreApplication.translate("WeekendDataExtraction", "Articolo di studio")

            dati = []
            # Popup per il cantico oratore modifica SOLO questa prima riga:
            dati.append(("cantico", c_label, "5:00"))
            # Discorso pubblico
            dati.append(("discorso", QCoreApplication.translate("WeekendDataExtraction", "Discorso pubblico"), "30:00"))
            # Cantico primo della Torre di Guardia (da pagina, senza popup)
            if len(songs) >= 1:
                dati.append(("cantico", f"{c_label} {songs[0]}", "5:00"))
            # Studio Torre di Guardia (titolo + 60)
            dati.append(("studio", title, "60:00"))
            # Cantico finale (da pagina, senza popup)
            if len(songs) >= 2:
                dati.append(("cantico", f"{c_label} {songs[1]}", "5:00"))

            if self.progress_callback:
                await self.progress_callback(100, QCoreApplication.translate("WeekendDataExtraction", "Estrazione completata"))
            return dati

        except asyncio.CancelledError:
            # Task cancellato: rilancia per gestione upstream
            logging.info("[Weekend] Estrazione dati cancellata")
            raise
        except GeneratorExit:
            # GeneratorExit: non rilanciare, ritorna lista vuota per evitare "Exception ignored"
            logging.info("[Weekend] GeneratorExit durante cancellazione - ritorno lista vuota")
            return []
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logging.exception("Errore di rete (weekend): %s", str(e))
            # Fallback GitHub: prova a scaricare il pacchetto .jwtimepack e a usare le righe da lì
            fallback_rows = await self._try_fallback_pack(week_id)
            return fallback_rows or []
        except Exception as e:
            logging.exception("Errore inatteso (weekend): %s", str(e))
            return []

    def _article_title(self, soup: BeautifulSoup) -> str:
        for tag in ["h1", "h2"]:
            h = soup.find(tag)
            if h:
                t = h.get_text(" ", strip=True)
                if t:
                    return t
        t = soup.find("title")
        return t.get_text(" ", strip=True) if t else ""

    async def _try_fallback_pack(self, week_id: str):
        """Prova a scaricare il pacchetto da GitHub e a restituire le rows."""
        url = build_pack_url(self.original_lang_code, "weekend", week_id)
        logging.info("[Weekend] Tentativo fallback GitHub: %s", url)

        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    content = await resp.read()

            # Salva su file temporaneo e importa con PackManager
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jwtimepack") as tmp:
                tmp.write(content)
                temp_path = Path(tmp.name)

            try:
                result = PackManager.import_packages(str(temp_path))
            finally:
                # Pulisce il file temporaneo
                with contextlib.suppress(Exception):
                    temp_path.unlink(missing_ok=True)

            if not result or not result.get("valid"):
                logging.warning("[Weekend] Pacchetto fallback non valido o vuoto")
                return []

            packages = result.get("packages") or []
            if not packages:
                logging.warning("[Weekend] Nessun pacchetto nel file fallback")
                return []

            pkg = packages[0]
            if pkg.program_type != "weekend":
                logging.warning("[Weekend] Pacchetto fallback di tipo diverso: %s", pkg.program_type)

            return pkg.rows

        except Exception as exc:
            logging.warning("[Weekend] Fallback GitHub fallito: %s", exc)
            return []
