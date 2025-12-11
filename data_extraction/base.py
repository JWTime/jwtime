import re
import logging
import unicodedata
from datetime import date, timedelta
from urllib.parse import urljoin

class DataExtractionBase:
    async def estrai_dati(self):
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────────────────────
# Utility comuni
# ─────────────────────────────────────────────────────────────────────────────
def normalize_lang_code(lang: str) -> str:
    """
    Normalizza i codici lingua dall'applicazione ai codici ISO standard.
    L'applicazione usa: it, en, fr, sp (spagnolo), td (tedesco)
    I codici ISO sono: it, en, fr, es (spagnolo), de (tedesco)
    """
    lang = (lang or "").lower().strip()
    if lang.startswith("it"):
        return "it"
    if lang.startswith("en"):
        return "en"
    if lang.startswith("fr"):
        return "fr"
    if lang.startswith("es") or lang == "sp":  # L'app usa 'sp' per spagnolo
        return "es"
    if lang.startswith("de") or lang == "td":  # L'app usa 'td' per tedesco
        return "de"
    return "it"


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"[^\w\s\-|]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_url(base_url: str, href: str) -> str:
    try:
        return urljoin(base_url, href)
    except Exception:
        return href or ""


# ─────────────────────────────────────────────────────────────────────────────
# Mappa lingua centralizzata
# ─────────────────────────────────────────────────────────────────────────────
_LANG = {
    "it": {
        "CANTICO": "Cantico",
        "NUOVA_CANZONE": "Nuova canzone",
        "NUOVA_CANZONE_ALIASES": ["nuova canzone", "nuova canzone del congresso", "canzone del congresso"],
        "INTRO": "Commenti introduttivi",
        "INTRO_ALIASES": ["Commenti introduttivi"],
        "OUTRO": "Commenti conclusivi",
        "OUTRO_ALIASES": ["Commenti conclusivi"],
        "LETTURA_BIBLICA": "Lettura biblica",
        "MONTHS": [
            "gennaio","febbraio","marzo","aprile","maggio","giugno",
            "luglio","agosto","settembre","ottobre","novembre","dicembre"
        ],
        "MINUTES_WORDS": ["min","min."],
        # Meeting links
        "MWB_LABELS": [
            "guida per l’adunanza vita e ministero",
            "guida per l'adunanza vita e ministero",
        ],
        "WT_LABELS": ["torre di guardia"],
        "ROUTE": ("r6", "lp-i"),
    },
    "en": {
        "CANTICO": "Song",
        "NUOVA_CANZONE": "New song",
        "NUOVA_CANZONE_ALIASES": ["new song", "new song for", "convention song"],
        "INTRO": "Opening Comments",
        "INTRO_ALIASES": ["opening comments"],
        "OUTRO": "Concluding Comments",
        "OUTRO_ALIASES": ["concluding comments"],
        "LETTURA_BIBLICA": "Bible Reading",
        "MONTHS": [
            "january","february","march","april","may","june",
            "july","august","september","october","november","december"
        ],
        "MINUTES_WORDS": ["min","min.","minutes"],
        "MWB_LABELS": ["life and ministry meeting workbook"],
        "WT_LABELS": ["the watchtower"],
        "ROUTE": ("r1", "lp-e"),
    },
    "fr": {
        "CANTICO": "Cantique",
        "NUOVA_CANZONE": "Nouvelle chanson",
        "NUOVA_CANZONE_ALIASES": [
            "nouveau cantique",
            "nouvelle chanson",
            "chanson de l'assemblee",
            "chanson de l assemblee",
            "cantique nouveau",
        ],
        "INTRO": "Paroles d'introduction",
        "INTRO_ALIASES": [
            "paroles d'introduction",
            "commentaires d'introduction",
            "commentaires introductifs",
        ],
        "OUTRO": "Paroles de conclusion",
        "OUTRO_ALIASES": [
            "paroles de conclusion",
            "commentaires de conclusion",
            "commentaire de conclusion",
            "remarques finales",
        ],
        "LETTURA_BIBLICA": "Lecture de la Bible",
        "MONTHS": [
            "janvier","février","mars","avril","mai","juin",
            "juillet","août","septembre","octobre","novembre","décembre"
        ],
        "MINUTES_WORDS": ["min","min."],
        "MWB_LABELS": ["cahier vie et ministère","cahier vie et ministere","guide de réunion vie et ministère","guide de la réunion vie et ministère","guide de la reunion vie et ministere"],
        "WT_LABELS": ["la tour de garde","la tour de garde (édition d’étude)","la tour de garde edition d etude"],
        "ROUTE": ("r30", "lp-f"),
    },
    "es": {
        "CANTICO": "Canción",
        "NUOVA_CANZONE": "Nueva canción",
        "NUOVA_CANZONE_ALIASES": ["nueva cancion", "nuevo cantico", "cancion de la asamblea", "cancion de asamblea"],
        "INTRO": "Palabras de introducción",
        "INTRO_ALIASES": ["palabras de introducción", "comentarios iniciales", "comentarios de apertura"],
        "OUTRO": "Palabras de conclusión",
        "OUTRO_ALIASES": ["palabras de conclusión", "comentarios finales", "comentarios de conclusión", "comentarios de cierre"],
        "LETTURA_BIBLICA": "Lectura de la Biblia",
        "MONTHS": [
            "enero","febrero","marzo","abril","mayo","junio",
            "julio","agosto","septiembre","octubre","noviembre","diciembre"
        ],
        "MINUTES_WORDS": ["min","min.","minutos","mins","mins."],
        # Label reali usati nelle settimane recenti
        "MWB_LABELS": [
            "guía de actividades",
            "guia de actividades",
            "guía para la reunión vida y ministerio",
            "guia para la reunion vida y ministerio",
            "guía de actividades de la reunión vida y ministerio",
            "guia de actividades de la reunion vida y ministerio",
        ],
        "WT_LABELS": ["la atalaya","la atalaya (edición de estudio)","la atalaya edicion de estudio"],
        "ROUTE": ("r4", "lp-s"),
    },
    "de": {
        "CANTICO": "Lied",
        "NUOVA_CANZONE": "Kongresslied",
        "NUOVA_CANZONE_ALIASES": ["neues lied", "neue hymne", "lied der versammlung", "kongresslied", "kongress lied"],
        "INTRO": "Einleitende Worte",
        "INTRO_ALIASES": ["einleitende worte", "einleitende kommentare", "einleitung"],
        "OUTRO": "Schlussworte",
        "OUTRO_ALIASES": ["schlussworte", "abschließende kommentare", "abschliessende kommentare", "schlussbemerkungen"],
        "LETTURA_BIBLICA": "Bibellesung",
        "MONTHS": [
            "januar","februar","märz","april","mai","juni",
            "juli","august","september","oktober","november","dezember"
        ],
        "MINUTES_WORDS": ["min","min.","minuten","Min","Min."],
        "MWB_LABELS": [
            "leben und dienst",
            "arbeitsheft leben und dienst",
            "leben und dienst - arbeitsheft",
            "leben und dienst: arbeitsheft",
            "arbeitsheft",
        ],
        "WT_LABELS": ["der wachtturm","der wachtturm studienausgabe","studienausgabe der wachtturm"],
        "ROUTE": ("r10", "lp-x"),
    },
    "pt_br": {
        "CANTICO": "Cântico",
        "NUOVA_CANZONE": "Cântico novo",
        "NUOVA_CANZONE_ALIASES": [
            "cântico novo",
            "cantico novo",
            "novo cântico",
            "novo cantico",
            "nova canção",
            "nova cancao",
            "canção da assembleia",
            "cancao da assembleia",
        ],
        "INTRO": "Comentários iniciais",
        "INTRO_ALIASES": ["comentários iniciais", "comentarios iniciais", "palavras iniciais"],
        "OUTRO": "Comentários finais",
        "OUTRO_ALIASES": ["comentários finais", "comentarios finais", "palavras finais"],
        "LETTURA_BIBLICA": "Leitura da Bíblia",
        "MONTHS": [
            "janeiro","fevereiro","março","abril","maio","junho",
            "julho","agosto","setembro","outubro","novembro","dezembro"
        ],
        "MINUTES_WORDS": ["min","min.","minutos","mins","mins."],
        "MWB_LABELS": [
            "apostila vida e ministério",
            "apostila vida e ministerio",
            "guia para a reunião vida e ministério",
            "guia para a reuniao vida e ministerio",
            "apostila",
        ],
        "WT_LABELS": ["a sentinela","a sentinela (estudo)","a sentinela estudo"],
        "ROUTE": ("r5", "lp-t"),
    },
}

def get_language_strings(lang_code: str) -> dict:
    # Special handling for pt_BR before normalization
    lang_lower = (lang_code or "").lower().strip()
    logging.info("[BASE DEBUG] get_language_strings called with lang_code='%s', normalized='%s'", lang_code, lang_lower)

    if lang_lower == "pt_br":
        result = _LANG.get("pt_br", _LANG["it"])
        logging.info("[BASE DEBUG] Returning pt_br dictionary, ROUTE=%s", result.get("ROUTE"))
        return result

    normalized = normalize_lang_code(lang_code)
    result = _LANG.get(normalized, _LANG["it"])
    logging.info("[BASE DEBUG] After normalization: '%s' -> returning dict with ROUTE=%s", normalized, result.get("ROUTE"))
    return result

def get_route_info(lang_code: str):
    logging.info("[BASE DEBUG] get_route_info called with lang_code='%s'", lang_code)
    lm = get_language_strings(lang_code)
    route = lm["ROUTE"]
    logging.info("[BASE DEBUG] get_route_info returning: %s", route)
    return route

def minutes_regex_for(lang_code: str):
    words = get_language_strings(lang_code)["MINUTES_WORDS"]
    pat = r"\((\d+)\s*(?:" + "|".join([re.escape(w) for w in words]) + r")\)"
    return re.compile(pat, re.IGNORECASE)


# ─────────────────────────────────────────────────────────────────────────────
# Rilevazione lingua pagina + correzione URL lingua/route
# ─────────────────────────────────────────────────────────────────────────────
def detect_page_lang_from_soup(soup) -> str:
    try:
        html = soup.find("html")
        if html and html.has_attr("lang"):
            cand = (html["lang"] or "").split("-")[0].lower()
            if cand in _LANG:
                return cand
        meta = soup.find("meta", attrs={"property": "og:locale"})
        if meta and meta.get("content"):
            cand = (meta["content"] or "").split("_")[0].lower()
            if cand in _LANG:
                return cand
    except Exception:
        pass
    return ""

def ensure_url_language(url: str, target_lang: str, route_tuple) -> str:
    """Riscrive /{xx}/wol/… e i segmenti /r#/ e /lp-…/ verso la lingua richiesta."""
    try:
        r_code, lp_code = route_tuple
        out = re.sub(r"/[a-z]{2}/wol/", f"/{target_lang}/wol/", url, count=1)
        out = re.sub(r"/r\d+/", f"/{r_code}/", out, count=1)
        out = re.sub(r"/lp-[a-z\-]+/", f"/{lp_code}/", out, count=1)
        return out
    except Exception:
        return url


# ─────────────────────────────────────────────────────────────────────────────
# Ricerca link (Workbook / Watchtower) sulla pagina della settimana
# ─────────────────────────────────────────────────────────────────────────────
def find_meeting_link(soup, base_url: str, lang_code: str, kind: str) -> str:
    """
    kind: 'workbook' | 'watchtower'
    Preferenza:
      1) <a> con etichetta corrispondente **e** href nella lingua richiesta
      2) <a> con etichetta corrispondente
      3) fallback su href che contenga token plausibili, privilegiando la lingua richiesta
    """
    # DON'T normalize here - use get_language_strings directly which handles pt_br
    lm = get_language_strings(lang_code)

    # For URL matching, we need the short form (pt_br -> pt for URL)
    lang_lower = (lang_code or "").lower().strip()
    if lang_lower == "pt_br":
        lang = "pt"  # For URL matching
    else:
        lang = normalize_lang_code(lang_code)

    labels = lm["MWB_LABELS"] if kind == "workbook" else lm["WT_LABELS"]
    labels_norm = [normalize_text(x) for x in labels]

    if kind == "workbook":
        href_tokens = [
            "mwb","workbook","life-and-ministry","leben-und-dienst","arbeitsheft",
            "guia","guía","reunion","reunión","vida-y-ministerio",
            "cahier","vie-et-ministere","vie-ministere","guida-adunanza",
            "apostila","vida-e-ministerio"
        ]
    else:
        href_tokens = [
            "watchtower","torre-di-guardia","atalaya","wachtturm","studienausgabe",
            "/wol/d/","tour-de-garde","torre-guardia","sentinela"
        ]

    candidates = []

    for a in soup.find_all("a", href=True):
        href = a.get("href") or ""
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        url = normalize_url(base_url, href)
        txt = normalize_text(a.get_text(" ", strip=True))
        text_match = any(lbl in txt for lbl in labels_norm)
        token_match = any(tok in href.lower() for tok in href_tokens)
        lang_ok = f"/{lang}/" in url  # preferisci URL già nella lingua richiesta

        if text_match or token_match:
            if text_match and lang_ok:
                score = 0
            elif text_match:
                score = 1
            elif token_match and lang_ok:
                score = 2
            else:
                score = 3
            candidates.append((score, url))

    if not candidates:
        return ""

    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


# ─────────────────────────────────────────────────────────────────────────────
# Settimana ISO + pattern di intestazione settimana
# ─────────────────────────────────────────────────────────────────────────────
def iso_week_range(anchor: date):
    monday = anchor - timedelta(days=(anchor.weekday()))
    sunday = monday + timedelta(days=6)
    return monday, sunday

def week_header_patterns(lang_code: str, week_monday: date, week_sunday: date):
    lm = get_language_strings(lang_code)
    months = lm["MONTHS"]
    mname = months[week_monday.month - 1] if week_monday.month - 1 < len(months) else ""
    d1, d2 = week_monday.day, week_sunday.day
    d1s, d2s, ms = str(d1), str(d2), normalize_text(mname)
    
    # Handle pt_br specially
    lang_lower = (lang_code or "").lower().strip()
    if lang_lower == "pt_br":
        lang = "pt"
    else:
        lang = normalize_lang_code(lang_code)

    pats = []

    if lang == "en":
        # English: "September 22-28" (month first)
        pats.append(re.compile(fr"{ms}\s+{d1s}\s*-\s*{d2s}"))
    elif lang == "de":
        # German: "22.–28. September" (with dots and long dash)
        pats.append(re.compile(fr"{d1s}\.?\s*[–-]\s*{d2s}\.?\s+{ms}"))
    elif lang == "es":
        # Spanish: "22-28 de septiembre" (with "de")
        pats.append(re.compile(fr"{d1s}\s*-\s*{d2s}\s+de\s+{ms}"))
    elif lang == "pt":
        # Portuguese: "22-28 de setembro" (with "de", same as Spanish)
        pats.append(re.compile(fr"{d1s}\s*-\s*{d2s}\s+de\s+{ms}"))
    else:
        # Italian, French: "22-28 settembre/septembre"
        pats.append(re.compile(fr"{d1s}\s*-\s*{d2s}\s+{ms}"))
    
    # Fallback patterns for all languages
    pats.append(re.compile(fr"{d1s}\s*-\s*{d2s}\s+{ms}"))
    pats.append(re.compile(fr"{ms}\s+{d1s}\s*-\s*{d2s}"))
    pats.append(re.compile(fr"{d1s}\.?\s*[–-]\s*{d2s}\.?\s+{ms}"))
    
    return pats
