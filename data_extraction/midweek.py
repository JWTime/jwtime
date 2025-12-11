import re
import aiohttp
import asyncio
import logging
import tempfile
import contextlib
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
from PyQt5.QtCore import QCoreApplication

from data_extraction.base import (
    DataExtractionBase,
    get_language_strings,
    normalize_lang_code,
    get_route_info,
    find_meeting_link,
    minutes_regex_for,
    normalize_text,
    iso_week_range,
    week_header_patterns,
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

CANTICO_DURATION = "5:00"


class MidweekDataExtraction(DataExtractionBase):
    def __init__(self, settimana_offset: int = 0, lang_code: str = "it", progress_callback=None):
        # Store the original language code (e.g., pt_BR)
        self.original_lang_code = (lang_code or "it").lower().strip()

        logging.info("[MIDWEEK DEBUG] __init__ called with lang_code='%s'", lang_code)
        logging.info("[MIDWEEK DEBUG] original_lang_code='%s'", self.original_lang_code)

        # For URL construction, convert pt_BR to pt
        if self.original_lang_code == "pt_br":
            self.request_lang = "pt"
        else:
            self.request_lang = normalize_lang_code(lang_code or "it")

        logging.info("[MIDWEEK DEBUG] request_lang='%s'", self.request_lang)

        self.settimana_offset = settimana_offset or 0
        # Use original code for getting language strings (pt_BR)
        self.lang_code = self.original_lang_code
        self.lang = get_language_strings(self.lang_code)

        logging.info("[MIDWEEK DEBUG] lang dictionary keys: %s", list(self.lang.keys()))
        logging.info("[MIDWEEK DEBUG] ROUTE from lang dict: %s", self.lang.get("ROUTE", "NOT FOUND"))

        self.progress_callback = progress_callback
        

    async def estrai_dati(self):
        try:
            anchor = datetime.now() + timedelta(weeks=self.settimana_offset)
            year, week = anchor.isocalendar()[0], anchor.isocalendar()[1]
            week_id = f"{year:04d}-{week:02d}"

            # costruisco la pagina settimana nella lingua RICHIESTA
            # Use original_lang_code (pt_BR) to get route info, use request_lang (pt) for URL
            logging.info("[MIDWEEK DEBUG] Getting route info for original_lang_code='%s'", self.original_lang_code)
            r_code, lp_code = get_route_info(self.original_lang_code)
            logging.info("[MIDWEEK DEBUG] Route info: r_code='%s', lp_code='%s'", r_code, lp_code)

            meetings_url = f"https://wol.jw.org/{self.request_lang}/wol/meetings/{r_code}/{lp_code}/{year}/{week}"
            logging.info("[MIDWEEK DEBUG] Constructed meetings_url: %s", meetings_url)

            headers = {
                "Accept-Language": build_accept_language(self.original_lang_code),
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JWTime/1.0",
            }
            logging.info("[MIDWEEK DEBUG] Accept-Language header: %s", headers["Accept-Language"])

            if self.progress_callback:
                await self.progress_callback(5, QCoreApplication.translate("MidweekDataExtraction", "Apro la pagina della settimana…"))

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(meetings_url) as resp:
                    resp.raise_for_status()
                    html = await resp.text()

                soup = BeautifulSoup(html, "html.parser")

                # ── Ricerca link Workbook (con label estese per lingua) ─────────
                # Use original_lang_code (pt_BR) to search for labels, not request_lang (pt)
                logging.info("[MIDWEEK DEBUG] Searching for workbook link with original_lang_code='%s', kind='workbook'", self.original_lang_code)
                workbook_url = find_meeting_link(soup, meetings_url, self.original_lang_code, kind="workbook")
                logging.info("[MIDWEEK DEBUG] Found workbook_url (before ensure): %s", workbook_url)

                if not workbook_url:
                    logging.warning("[Midweek] Link Workbook non trovato per la lingua %s", self.request_lang)
                    if self.progress_callback:
                        await self.progress_callback(100, "[Midweek] Link Workbook non trovato per la lingua " + self.request_lang.upper())
                    return []

                # riscrivo SEMPRE i segmenti verso la lingua richiesta
                workbook_url = ensure_url_language(workbook_url, self.request_lang, (r_code, lp_code))
                logging.info("[MIDWEEK DEBUG] Final workbook_url (after ensure): %s", workbook_url)

                if self.progress_callback:
                    await self.progress_callback(20, QCoreApplication.translate("MidweekDataExtraction", "Apro la pagina del Workbook…"))

                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(workbook_url) as resp:
                        resp.raise_for_status()
                        wb_html = await resp.text()

            wb = BeautifulSoup(wb_html, "html.parser")

            # Rileva la lingua della pagina per il parsing, ma mantieni la lingua richiesta per l'interfaccia
            detected_page_lang = detect_page_lang_from_soup(wb)
            logging.info("[MIDWEEK DEBUG] Detected page language: %s", detected_page_lang)

            if detected_page_lang and detected_page_lang != self.request_lang:
                logging.warning("[Midweek] Page language is %s but requested %s. Using page language for parsing.", detected_page_lang, self.request_lang)

            # Use original_lang_code for parsing (pt_BR), not request_lang (pt)
            # The detected page lang is usually just 'pt' but we need 'pt_br' for our dictionary
            parsing_lang = self.original_lang_code
            logging.info("[MIDWEEK DEBUG] Using parsing_lang: %s (forced to original_lang_code)", parsing_lang)
            logging.info("[MIDWEEK DEBUG] Using UI lang_code: %s", self.lang_code)

            page_type = "weekly" if "/wol/d/" in workbook_url else "monthly"

            block_root = wb if page_type == "weekly" else (self._slice_week_block(wb, anchor.date(), parsing_lang) or wb)
            if block_root is wb and page_type != "weekly":
                logging.warning("[Midweek] Intestazione settimana non trovata; uso tutta la pagina.")

            dati = self._parse_week_block(block_root, parsing_lang)

            if not dati:
                dati.append(("parte", QCoreApplication.translate("MidweekDataExtraction", "Contenuti non riconosciuti"), "1:00"))

            if self.progress_callback:
                await self.progress_callback(100, QCoreApplication.translate("MidweekDataExtraction", "Estrazione completata"))
            return dati

        except asyncio.CancelledError:
            # Task cancellato: rilancia per gestione upstream
            logging.info("[Midweek] Estrazione dati cancellata")
            raise
        except GeneratorExit:
            # GeneratorExit: non rilanciare, ritorna lista vuota per evitare "Exception ignored"
            logging.info("[Midweek] GeneratorExit durante cancellazione - ritorno lista vuota")
            return []
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logging.exception("Errore di rete (midweek): %s", str(e))
            # Fallback GitHub: prova a scaricare il pacchetto .jwtimepack e a usare le righe da lì
            fallback_rows = await self._try_fallback_pack(week_id)
            return fallback_rows or []
        except Exception as e:
            logging.exception("Errore inatteso (midweek): %s", str(e))
            return []

    def _slice_week_block(self, soup_wb: BeautifulSoup, anchor_date: date, parsing_lang_code: str = None):
        monday, sunday = iso_week_range(anchor_date)
        parsing_lang_code = parsing_lang_code or self.lang_code
        pats = week_header_patterns(parsing_lang_code, monday, sunday)

        found = None
        for el in soup_wb.find_all(True):
            txtn = normalize_text(el.get_text(" ", strip=True))
            if txtn and any(p.search(txtn) for p in pats):
                found = el
                break
        if not found:
            return None
        parent = found.parent
        if not parent:
            return None

        from bs4 import Tag
        container = BeautifulSoup("<div></div>", "html.parser")
        root_div: Tag = container.div  # type: ignore

        take = False
        for child in list(parent.children):
            if not hasattr(child, "get_text"):
                continue
            txtn = normalize_text(child.get_text(" ", strip=True))
            if child is found:
                take = True
            if take:
                root_div.append(child)
                if child is not found and any(p.search(txtn) for p in pats):
                    root_div.contents.pop()
                    break

        return root_div

    def _parse_week_block(self, block_root: BeautifulSoup, parsing_lang_code: str = None):
        # Usa la lingua di parsing per riconoscere il contenuto della pagina
        parsing_lang_code = parsing_lang_code or self.lang_code
        page_lang = get_language_strings(parsing_lang_code)
        
        # Usa la lingua richiesta per i testi dell'interfaccia utente
        ui_lang = self.lang
        
        # Termini per riconoscimento (lingua della pagina)
        PAGE_CANTICO = page_lang["CANTICO"]
        PAGE_INTRO = page_lang["INTRO"]
        PAGE_OUTRO = page_lang["OUTRO"]
        INTRO_SET = [normalize_text(s) for s in page_lang.get("INTRO_ALIASES", [PAGE_INTRO])]
        OUTRO_SET = [normalize_text(s) for s in page_lang.get("OUTRO_ALIASES", [PAGE_OUTRO])]
        PAGE_LETTURA_BIBLICA = page_lang["LETTURA_BIBLICA"]
        
        # Termini per "nuova canzone" (lingua della pagina)
        PAGE_NUOVA_CANZONE_ALIASES = [normalize_text(s) for s in page_lang.get("NUOVA_CANZONE_ALIASES", [])]
        
        # Termini per etichette (lingua dell'interfaccia)
        UI_CANTICO = ui_lang["CANTICO"]
        UI_NUOVA_CANZONE = ui_lang["NUOVA_CANZONE"]
        UI_INTRO = ui_lang["INTRO"]
        UI_OUTRO = ui_lang["OUTRO"]
        UI_LETTURA_BIBLICA = ui_lang["LETTURA_BIBLICA"]
        
        MIN_RX = minutes_regex_for(parsing_lang_code)

        dati = []
        seen = set()
        seen_numbers = set()
        bible_reading_present = False

        def add_row(tipo: str, label: str, durata: str):
            key = (tipo, normalize_text(label))
            if key in seen:
                return
            seen.add(key)
            dati.append((tipo, label.strip(), durata))

        nodes = block_root.find_all(["h1","h2","h3","h4","h5","p","div","span","a","li"], recursive=True)
        heading_names = ("h1","h2","h3","h4","h5")
        num_rx = re.compile(r"^\s*(\d+)\.\s+(.*)")
        
        # Regex per cantici con esclusione di "HOHES LIED" (libro biblico in tedesco)
        # Per il tedesco, dobbiamo escludere "hohes", "hohe" e "das hohe" prima di "lied"
        if parsing_lang_code == "de":
            # Usa negative lookbehind per escludere varianti di "Hohes Lied"
            song_rx = re.compile(r"(?<!hohes\s)(?<!hohe\s)(?<!hohes)(?<!hohe)lied\s+(\d+)")
        else:
            song_rx = re.compile(rf"{re.escape(normalize_text(PAGE_CANTICO))}\s+(\d+)")
        
        lettura_norm = normalize_text(PAGE_LETTURA_BIBLICA)

        wait_duration_for_number = None

        def has_any(aliases, text_norm: str) -> bool:
            return any(a in text_norm for a in aliases)

        for el in nodes:
            txt_raw = el.get_text(" ", strip=True) or ""
            if not txt_raw:
                continue
            txt = normalize_text(txt_raw)

            # Filtra elementi contenitore troppo grandi (> 1000 caratteri)
            # Questi sono probabilmente div wrapper che contengono tutto il contenuto della pagina
            # e possono causare falsi match quando cercano "Nuova canzone" nell'intero testo
            if len(txt_raw) > 1000:
                continue

            # Filtra elementi che sono solo date (pattern tedesco: "29. SEPTEMBER – 5. OKTOBER")
            # Pattern generale per date con mesi
            months = page_lang.get("MONTHS", [])
            if months:
                # Controlla se il testo contiene pattern di intervallo date
                is_date_range = False
                for month in months:
                    if month.lower() in txt.lower():
                        # Verifica se sembra un intervallo di date (contiene numeri, mesi e trattini/dash)
                        if any(dash in txt_raw for dash in ["–", "-", "—"]):
                            # Conta quanti mesi ci sono nel testo
                            month_count = sum(1 for m in months if m.lower() in txt.lower())
                            # Se ci sono 2 mesi e numeri, probabilmente è un intervallo di date
                            if month_count >= 1 and any(char.isdigit() for char in txt_raw):
                                # Verifica che non ci siano altri contenuti significativi
                                # (solo numeri, mesi, punti e trattini)
                                words = txt_raw.replace(".", " ").replace("–", " ").replace("-", " ").split()
                                significant_words = [w for w in words if w and not w.isdigit() and w.upper() not in [m.upper() for m in months]]
                                if len(significant_words) <= 1:  # Solo congiunzioni o articoli
                                    is_date_range = True
                                    break
                
                if is_date_range:
                    continue  # Salta questo elemento

            # Prima controlla se è una nuova canzone (deve essere fatto PRIMA di has_song)
            # per evitare che "Kongresslied 2025" venga interpretato come "Lied 2025"
            has_new_song = has_any(PAGE_NUOVA_CANZONE_ALIASES, txt)
            
            # Se è una nuova canzone, non cercare pattern di cantico normale
            has_song = False if has_new_song else bool(song_rx.search(txt))
            
            has_intro = has_any(INTRO_SET, txt)
            has_outro = has_any(OUTRO_SET, txt)

            # ── Cantico + intro/outro sulla stessa riga (anche ordine inverso) ──
            if has_song and has_intro:
                m = song_rx.search(txt)
                add_row("cantico", f"{UI_CANTICO} {m.group(1)}", CANTICO_DURATION)
                md = MIN_RX.search(txt_raw)
                add_row("commento_introduttivo", UI_INTRO, clock(md.group(1)) if md else "1:00")
                continue

            if has_song and has_outro:
                md = MIN_RX.search(txt_raw)
                add_row("commento_conclusivo", UI_OUTRO, clock(md.group(1)) if md else "3:00")
                m = song_rx.search(txt)
                add_row("cantico", f"{UI_CANTICO} {m.group(1)}", CANTICO_DURATION)
                continue

            # ── Nuova canzone + intro/outro sulla stessa riga ──
            if has_new_song and has_intro:
                add_row("cantico", UI_NUOVA_CANZONE, CANTICO_DURATION)
                md = MIN_RX.search(txt_raw)
                add_row("commento_introduttivo", UI_INTRO, clock(md.group(1)) if md else "1:00")
                continue

            if has_new_song and has_outro:
                md = MIN_RX.search(txt_raw)
                add_row("commento_conclusivo", UI_OUTRO, clock(md.group(1)) if md else "3:00")
                add_row("cantico", UI_NUOVA_CANZONE, CANTICO_DURATION)
                continue

            if has_song:
                m = song_rx.search(txt)
                add_row("cantico", f"{UI_CANTICO} {m.group(1)}", CANTICO_DURATION)
                continue

            # ── Nuova canzone da sola ──
            if has_new_song:
                add_row("cantico", UI_NUOVA_CANZONE, CANTICO_DURATION)
                continue

            if has_intro and not any(normalize_text(x[1]) in INTRO_SET for x in dati):
                md = MIN_RX.search(txt_raw)
                add_row("commento_introduttivo", UI_INTRO, clock(md.group(1)) if md else "1:00")
                continue

            if has_outro and not any(normalize_text(x[1]) in OUTRO_SET for x in dati):
                md = MIN_RX.search(txt_raw)
                add_row("commento_conclusivo", UI_OUTRO, clock(md.group(1)) if md else "3:00")
                continue

            # Parti numerate SOLO se l'elemento è un heading
            if el.name in heading_names:
                mn = num_rx.match(txt_raw)
                if mn:
                    numero = mn.group(1)
                    if numero in seen_numbers:
                        wait_duration_for_number = None
                        continue

                    titolo = mn.group(2).strip()
                    titolo_pulito = MIN_RX.sub("", titolo).strip()

                    add_row("parte_numerata", f"{numero}. {titolo_pulito}", "1:00")
                    seen_numbers.add(numero)
                    wait_duration_for_number = numero

                    if lettura_norm and lettura_norm in normalize_text(titolo_pulito):
                        bible_reading_present = True
                    continue

            if wait_duration_for_number is not None:
                md = MIN_RX.search(txt_raw)
                if md:
                    durata = clock(md.group(1))
                    for idx in range(len(dati) - 1, -1, -1):
                        t, label, _ = dati[idx]
                        if t == "parte_numerata" and label.startswith(f"{wait_duration_for_number}."):
                            dati[idx] = (t, label, durata)
                            break
                    wait_duration_for_number = None
                continue

            # Lettura biblica solo su heading con etichetta (evita paragrafi descrittivi)
            if el.name in heading_names:
                if lettura_norm and (txt.startswith(lettura_norm) or txt == lettura_norm) and not bible_reading_present:
                    md = MIN_RX.search(txt_raw)
                    add_row("parte", MIN_RX.sub("", el.get_text(' ', strip=True)).strip(), clock(md.group(1)) if md else "4:00")
                    bible_reading_present = True
                    continue

        # NB: nessun “riempitivo” per FR — se intro/outro non sono presenti nella pagina, non li aggiungiamo.
        return dati

    async def _try_fallback_pack(self, week_id: str):
        """Prova a scaricare il pacchetto da GitHub e a restituire le rows."""
        url = build_pack_url(self.original_lang_code, "midweek", week_id)
        logging.info("[Midweek] Tentativo fallback GitHub: %s", url)

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
                logging.warning("[Midweek] Pacchetto fallback non valido o vuoto")
                return []

            packages = result.get("packages") or []
            if not packages:
                logging.warning("[Midweek] Nessun pacchetto nel file fallback")
                return []

            pkg = packages[0]
            if pkg.program_type != "midweek":
                logging.warning("[Midweek] Pacchetto fallback di tipo diverso: %s", pkg.program_type)

            return pkg.rows

        except Exception as exc:
            logging.warning("[Midweek] Fallback GitHub fallito: %s", exc)
            return []
