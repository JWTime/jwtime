# file: utils/week_formatter.py

"""
Formattazione settimane secondo il locale, senza anno.
Esempi:
- "20 – 26 ott." (italiano)
- "Oct 20 – 26" (inglese)
- "27 ott. – 2 nov." (a cavallo mese, italiano)
- "30 dic. – 5 gen." (a cavallo anno, italiano)
"""

from datetime import datetime, timedelta
from typing import Tuple
import locale as py_locale


class WeekRangeFormatter:
    """Formatta range di settimana secondo il locale, senza anno."""

    # Mapping codici lingua -> locale system
    LOCALE_MAP = {
        'it': ('it_IT', 'Italian_Italy'),
        'en': ('en_US', 'English_United States'),
        'fr': ('fr_FR', 'French_France'),
        'es': ('es_ES', 'Spanish_Spain'),
        'de': ('de_DE', 'German_Germany'),
        'pt_br': ('pt_BR', 'Portuguese_Brazil'),
    }

    # Abbreviazioni mesi per lingua (fallback se locale non disponibile)
    MONTH_ABBR = {
        'it': ['gen.', 'feb.', 'mar.', 'apr.', 'mag.', 'giu.',
               'lug.', 'ago.', 'set.', 'ott.', 'nov.', 'dic.'],
        'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'fr': ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin',
               'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'],
        'es': ['ene.', 'feb.', 'mar.', 'abr.', 'mayo', 'jun.',
               'jul.', 'ago.', 'sept.', 'oct.', 'nov.', 'dic.'],
        'de': ['Jan.', 'Feb.', 'März', 'Apr.', 'Mai', 'Juni',
               'Juli', 'Aug.', 'Sept.', 'Okt.', 'Nov.', 'Dez.'],
        'pt_br': ['jan.', 'fev.', 'mar.', 'abr.', 'maio', 'jun.',
                  'jul.', 'ago.', 'set.', 'out.', 'nov.', 'dez.'],
    }

    def __init__(self, lang_code: str = 'it'):
        """
        Inizializza formatter con codice lingua.

        Args:
            lang_code: Codice lingua (it, en, fr, es, de, pt_br)
        """
        self.lang_code = lang_code.lower()
        if self.lang_code not in self.LOCALE_MAP:
            self.lang_code = 'it'  # Fallback

        self._setup_locale()

    def _setup_locale(self):
        """Configura locale di sistema se disponibile."""
        locale_variants = self.LOCALE_MAP.get(self.lang_code, ('it_IT', 'Italian_Italy'))

        for loc in locale_variants:
            try:
                py_locale.setlocale(py_locale.LC_TIME, loc)
                return
            except (py_locale.Error, Exception):
                continue

        # Fallback a C locale se tutto fallisce
        try:
            py_locale.setlocale(py_locale.LC_TIME, 'C')
        except:
            pass

    def get_week_range(self, week_offset: int = 0) -> Tuple[datetime, datetime]:
        """
        Calcola il range (lunedì-domenica) della settimana ISO.

        Args:
            week_offset: Offset settimane da oggi (0=corrente, +1=prossima, -1=precedente)

        Returns:
            Tuple (monday, sunday) come datetime objects
        """
        today = datetime.now()
        anchor = today + timedelta(weeks=week_offset)

        # Calcola lunedì della settimana ISO
        iso_year, iso_week, iso_weekday = anchor.isocalendar()

        # Trova il lunedì di questa settimana ISO
        # isocalendar() restituisce weekday: 1=lunedì, 7=domenica
        monday = anchor - timedelta(days=iso_weekday - 1)
        sunday = monday + timedelta(days=6)

        return monday, sunday

    def format_week_range(self, week_offset: int = 0) -> str:
        """
        Formatta il range settimana senza anno.

        Args:
            week_offset: Offset settimane da oggi

        Returns:
            Stringa formattata tipo "20–26 ott." o "27 ott. – 2 nov."
        """
        monday, sunday = self.get_week_range(week_offset)

        # Usa en dash (–) non hyphen (-)
        # Unicode U+2013
        en_dash = "\u2013"

        # Stesso mese
        if monday.month == sunday.month:
            return self._format_same_month(monday, sunday, en_dash)
        else:
            return self._format_different_months(monday, sunday, en_dash)

    def _get_month_abbr(self, date: datetime) -> str:
        """Ottiene abbreviazione mese (con fallback)."""
        month_names = self.MONTH_ABBR.get(self.lang_code, self.MONTH_ABBR['it'])
        return month_names[date.month - 1]

    def _format_same_month(self, monday: datetime, sunday: datetime, separator: str) -> str:
        """Formatta range nello stesso mese."""
        month_abbr = self._get_month_abbr(monday)

        if self.lang_code == 'en':
            # Inglese: "Oct 20 – 26"
            return f"{month_abbr} {monday.day} {separator} {sunday.day}"
        elif self.lang_code == 'de':
            # Tedesco: "20. – 26. Okt."
            return f"{monday.day}. {separator} {sunday.day}. {month_abbr}"
        else:
            # Italiano, francese, spagnolo, portoghese: "20 – 26 ott."
            return f"{monday.day} {separator} {sunday.day} {month_abbr}"

    def _format_different_months(self, monday: datetime, sunday: datetime, separator: str) -> str:
        """Formatta range a cavallo di due mesi."""
        monday_month = self._get_month_abbr(monday)
        sunday_month = self._get_month_abbr(sunday)

        if self.lang_code == 'en':
            # Inglese: "Oct 27 – Nov 2"
            return f"{monday_month} {monday.day} {separator} {sunday_month} {sunday.day}"
        elif self.lang_code == 'de':
            # Tedesco: "27. Okt. – 2. Nov."
            return f"{monday.day}. {monday_month} {separator} {sunday.day}. {sunday_month}"
        elif self.lang_code in ('es', 'pt_br'):
            # Spagnolo/Portoghese: "27 de oct. – 2 de nov."
            return f"{monday.day} de {monday_month} {separator} {sunday.day} de {sunday_month}"
        else:
            # Italiano, francese: "27 ott. – 2 nov."
            return f"{monday.day} {monday_month} {separator} {sunday.day} {sunday_month}"

    def get_iso_week_number(self, week_offset: int = 0) -> int:
        """
        Restituisce il numero settimana ISO (1-53).

        Args:
            week_offset: Offset settimane da oggi

        Returns:
            Numero settimana ISO (1-53)
        """
        monday, _ = self.get_week_range(week_offset)
        return monday.isocalendar()[1]

    def format_week_with_number(self, week_offset: int = 0) -> str:
        """
        Formatta range settimana con numero ISO.

        Args:
            week_offset: Offset settimane da oggi

        Returns:
            Stringa tipo "W43: 20–26 ott."
        """
        week_num = self.get_iso_week_number(week_offset)
        week_range = self.format_week_range(week_offset)
        return f"W{week_num}: {week_range}"


# Funzioni di convenienza
def format_week(week_offset: int = 0, lang_code: str = 'it') -> str:
    """
    Formatta range settimana senza anno.

    Args:
        week_offset: Offset settimane da oggi (0=corrente, +1=prossima, -1=precedente)
        lang_code: Codice lingua (it, en, fr, es, de, pt_br)

    Returns:
        Stringa formattata tipo "20–26 ott."
    """
    formatter = WeekRangeFormatter(lang_code)
    return formatter.format_week_range(week_offset)


def get_week_iso_number(week_offset: int = 0) -> int:
    """
    Ottiene numero settimana ISO.

    Args:
        week_offset: Offset settimane da oggi

    Returns:
        Numero settimana ISO (1-53)
    """
    formatter = WeekRangeFormatter()
    return formatter.get_iso_week_number(week_offset)
