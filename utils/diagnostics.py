# file: utils/diagnostics.py

import asyncio
import contextlib
import json
import os
import random
import shutil
import socket
import struct
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import aiohttp
from bs4 import BeautifulSoup

from data_extraction.base import (
    find_meeting_link,
    get_route_info,
    normalize_lang_code,
)
from backup.backup_manager import get_iso_week_id
from utils.github_packs import build_pack_url


@dataclass
class DiagnosticResult:
    """Risultato singolo del test di connessione/ambiente."""

    name: str
    status: str  # ok | warning | error | info
    details: str


def _detect_proxy_env() -> Sequence[Tuple[str, str]]:
    """Restituisce elenco (variabile, valore) delle variabili proxy attive."""
    proxies: List[Tuple[str, str]] = []
    for key in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"):
        value = os.getenv(key)
        if value:
            proxies.append((key, value))
    return proxies


def get_log_dir() -> Path:
    custom_dir = os.getenv("JW_TIME_LOG_DIR")
    if custom_dir:
        return Path(custom_dir)
    appdata = os.getenv("APPDATA") or os.path.expanduser("~")
    return Path(appdata) / "JWTimeLogs"


def _get_local_state_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
    return Path(base) / "JWTimeApp" / "LocalState"


def _request_lang_from_setting(lang_code: str) -> str:
    lang = (lang_code or "it").lower().strip()
    if lang == "pt_br":
        return "pt"
    return normalize_lang_code(lang_code or "it")


def _build_accept_language(lang_code: str) -> str:
    lang = (lang_code or "it").lower().strip()
    if lang == "pt_br":
        return "pt-BR,pt;q=0.9,en;q=0.8"
    mapping = {
        "it": "it-IT,it;q=0.9,en;q=0.8",
        "en": "en-US,en;q=0.9",
        "fr": "fr-FR,fr;q=0.9,en;q=0.8",
        "es": "es-ES,es;q=0.9,en;q=0.8",
        "de": "de-DE,de;q=0.9,en;q=0.8",
        "pt": "pt-BR,pt;q=0.9,en;q=0.8",
    }
    return mapping.get(normalize_lang_code(lang_code or "it"), "it-IT,it;q=0.9,en;q=0.8")


async def _resolve_host(host: str) -> DiagnosticResult:
    loop = asyncio.get_running_loop()
    try:
        ip = await loop.run_in_executor(None, socket.gethostbyname, host)
        return DiagnosticResult("DNS wol.jw.org", "ok", f"{host} -> {ip}")
    except Exception as exc:  # pragma: no cover - dipende da rete
        return DiagnosticResult("DNS wol.jw.org", "error", str(exc))


async def _https_probe(url: str, headers: dict, label: str = "Connessione HTTPS") -> DiagnosticResult:
    timeout = aiohttp.ClientTimeout(total=10)
    last_error: Optional[Exception] = None
    for attempt in range(2):
        try:
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                async with session.get(url, allow_redirects=True) as resp:
                    reason = resp.reason or "OK"
                    return DiagnosticResult(
                        label,
                        "ok",
                        f"{url} risponde con {resp.status} {reason}",
                    )
        except aiohttp.ClientConnectorCertificateError as exc:  # pragma: no cover
            return DiagnosticResult(label, "error", f"Certificato non valido: {exc}")
        except Exception as exc:  # pragma: no cover
            last_error = exc
    message = ""
    if last_error:
        message = str(last_error).strip() or last_error.__class__.__name__
    return DiagnosticResult(label, "error", message or "Errore sconosciuto")


async def _workbook_probe(lang_code: str) -> List[DiagnosticResult]:
    original_lang = (lang_code or "it").lower().strip()
    request_lang = _request_lang_from_setting(lang_code)
    r_code, lp_code = get_route_info(original_lang)
    year, week = datetime.now().isocalendar()[0:2]
    meetings_url = f"https://wol.jw.org/{request_lang}/wol/meetings/{r_code}/{lp_code}/{year}/{week}"

    headers = {
        "Accept-Language": _build_accept_language(original_lang),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JWTime/diagnostic",
    }

    timeout = aiohttp.ClientTimeout(total=15)
    results: List[DiagnosticResult] = []

    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(meetings_url) as resp:
                resp.raise_for_status()
                html = await resp.text()

        results.append(
            DiagnosticResult(
                "Pagina settimana",
                "ok",
                f"Accesso riuscito ({request_lang.upper()})",
            )
        )

        soup = BeautifulSoup(html, "html.parser")
        workbook_link = find_meeting_link(soup, meetings_url, original_lang, kind="workbook")
        if not workbook_link:
            results.append(
                DiagnosticResult(
                    "Programma settimanale",
                    "warning",
                    "Etichette non riconosciute nella pagina (controlla lingua/filtri)",
                )
            )
            return results

        results.append(
            DiagnosticResult(
                "Programma settimanale",
                "ok",
                "Trovato collegamento per il programma",
            )
        )

        # Verifica l'apertura del workbook stesso
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(workbook_link) as resp:
                resp.raise_for_status()
                await resp.text()

        results.append(
            DiagnosticResult(
                "Download programma",
                "ok",
                "Il programma settimanale risponde correttamente",
            )
        )
    except aiohttp.ClientResponseError as exc:  # pragma: no cover
        results.append(
            DiagnosticResult(
                "Pagina settimana",
                "error",
                f"HTTP {exc.status} {exc.message}",
            )
        )
    except Exception as exc:  # pragma: no cover
        results.append(
            DiagnosticResult(
                "Pagina settimana",
                "error",
                str(exc),
            )
        )

    return results


async def _github_pack_probe(lang_code: str) -> DiagnosticResult:
    """
    Verifica se il pack fallback GitHub è raggiungibile per la settimana corrente.
    """
    week_id = get_iso_week_id(0)
    url = build_pack_url(lang_code, "midweek", week_id)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JWTime/diagnostic",
    }
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return DiagnosticResult(
                        "Fallback GitHub",
                        "ok",
                        f"Pack {week_id} disponibile ({resp.status})",
                    )
                return DiagnosticResult(
                    "Fallback GitHub",
                    "warning",
                    f"{resp.status} {resp.reason} per {week_id}",
                )
    except Exception as exc:  # pragma: no cover
        return DiagnosticResult("Fallback GitHub", "warning", str(exc))


def _directory_write_test(title: str, path: Path) -> DiagnosticResult:
    try:
        path.mkdir(parents=True, exist_ok=True)
        tmp_file = path / f".jwtest_{int(time.time() * 1000)}.tmp"
        tmp_file.write_text("diagnostic", encoding="utf-8")
        tmp_file.unlink(missing_ok=True)
        return DiagnosticResult(title, "ok", str(path))
    except Exception as exc:  # pragma: no cover
        return DiagnosticResult(title, "error", f"{path}: {exc}")


def _disk_space_test(path: Path, min_mb: int = 200) -> DiagnosticResult:
    try:
        total, used, free = shutil.disk_usage(path)
        free_mb = free / (1024 * 1024)
        status = "ok" if free_mb >= min_mb else "warning"
        return DiagnosticResult(
            "Spazio libero",
            status,
            f"{free_mb:.1f} MB",
        )
    except Exception as exc:  # pragma: no cover
        return DiagnosticResult("Spazio libero", "warning", f"Impossibile determinare: {exc}")


async def _tcp_latency_test(host: str, port: int = 443) -> DiagnosticResult:
    start = time.perf_counter()
    try:
        conn = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5)
        reader, writer = conn
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()
        elapsed_ms = (time.perf_counter() - start) * 1000
        return DiagnosticResult(
            "Latenza TLS wol.jw.org",
            "ok",
            f"{elapsed_ms:.0f} ms",
        )
    except Exception as exc:  # pragma: no cover
        return DiagnosticResult("Latenza TLS wol.jw.org", "warning", str(exc))


async def _proxy_probe(proxy_url: str, headers: dict) -> DiagnosticResult:
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get("https://wol.jw.org", proxy=proxy_url) as resp:
                resp.raise_for_status()
                return DiagnosticResult(
                    f"Proxy {proxy_url}",
                    "ok",
                    f"HTTP {resp.status}",
                )
    except Exception as exc:  # pragma: no cover
        return DiagnosticResult(
            f"Proxy {proxy_url}",
            "warning",
            str(exc),
        )


async def _doh_lookup(host: str) -> DiagnosticResult:
    url = f"https://cloudflare-dns.com/dns-query?name={host}&type=A"
    headers = {
        "accept": "application/dns-json",
    }
    timeout = aiohttp.ClientTimeout(total=8)
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                text = await resp.text()
                data = json.loads(text)
    except Exception as exc:  # pragma: no cover
        return DiagnosticResult("DNS DoH (Cloudflare)", "warning", str(exc))

    answers = data.get("Answer") or []
    ips = [ans.get("data") for ans in answers if ans.get("type") == 1 and ans.get("data")]
    if not ips:
        return DiagnosticResult("DNS DoH (Cloudflare)", "warning", "Nessuna risposta valida")
    return DiagnosticResult("DNS DoH (Cloudflare)", "ok", ", ".join(ips))


def _build_dns_query(name: str) -> bytes:
    transaction_id = random.randint(0, 0xFFFF)
    flags = 0x0100
    qdcount = 1
    header = struct.pack("!HHHHHH", transaction_id, flags, qdcount, 0, 0, 0)
    labels = name.strip(".").split(".")
    qname = b"".join(struct.pack("B", len(label)) + label.encode("ascii") for label in labels) + b"\x00"
    question = struct.pack("!HH", 1, 1)
    return header + qname + question, transaction_id


def _parse_dns_response(data: bytes, transaction_id: int) -> Tuple[str, List[str]]:
    if len(data) < 12:
        return "Risposta DNS troppo corta", []
    resp_tid, flags, qdcount, ancount, _, _ = struct.unpack("!HHHHHH", data[:12])
    if resp_tid != transaction_id:
        return "ID transazione non corrispondente", []
    rcode = flags & 0x000F
    if rcode != 0:
        return f"RCODE={rcode}", []
    offset = 12
    # salta le domande
    for _ in range(qdcount):
        while offset < len(data) and data[offset] != 0:
            offset += data[offset] + 1
        offset += 1  # byte nullo
        offset += 4  # tipo + classe
    ips: List[str] = []
    for _ in range(ancount):
        if offset + 12 > len(data):
            break
        offset += 2  # nome (pointer)
        rtype, rclass, ttl, rdlength = struct.unpack("!HHIH", data[offset:offset + 10])
        offset += 10
        rdata = data[offset:offset + rdlength]
        offset += rdlength
        if rtype == 1 and rclass == 1 and rdlength == 4:
            ips.append(".".join(str(b) for b in rdata))
    if not ips:
        return "Nessun record A", []
    return "", ips


async def _udp_dns_lookup(host: str, server: str = "1.1.1.1") -> DiagnosticResult:
    loop = asyncio.get_running_loop()

    def lookup():
        query, transaction_id = _build_dns_query(host)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(3)
            sock.sendto(query, (server, 53))
            data, _ = sock.recvfrom(512)
        error, ips = _parse_dns_response(data, transaction_id)
        if error:
            raise RuntimeError(error)
        return ips

    try:
        ips = await loop.run_in_executor(None, lookup)
        return DiagnosticResult(f"DNS UDP ({server})", "ok", ", ".join(ips))
    except Exception as exc:  # pragma: no cover
        return DiagnosticResult(f"DNS UDP ({server})", "warning", str(exc))


async def _certificate_probe(url: str, headers: dict) -> DiagnosticResult:
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(url, allow_redirects=True) as resp:
                resp.raise_for_status()
        return DiagnosticResult("Certificati di rete", "ok", "Il certificato presentato è attendibile")
    except aiohttp.ClientConnectorCertificateError as exc:  # pragma: no cover
        return DiagnosticResult(
            "Certificati di rete",
            "warning",
            f"Certificato non attendibile: {exc.host}",
        )
    except Exception as exc:  # pragma: no cover
        details = str(exc).strip() or exc.__class__.__name__
        return DiagnosticResult("Certificati di rete", "error", details)


async def _system_clock_check(headers: dict, max_skew_seconds: int = 120) -> DiagnosticResult:
    """
    Confronta l'orologio locale con l'intestazione Date di un server HTTPS.
    Segnala errore se la differenza supera la soglia (default 2 minuti).
    """
    url = "https://www.microsoft.com"
    timeout = aiohttp.ClientTimeout(total=10)

    async def _request_date(session: aiohttp.ClientSession) -> Optional[str]:
        for method in ("HEAD", "GET"):
            async with session.request(method, url, allow_redirects=True) as resp:
                date_header = resp.headers.get("Date")
                if date_header:
                    return date_header
        return None

    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            date_header = await _request_date(session)
    except Exception as exc:  # pragma: no cover - dipende dalla rete
        details = str(exc).strip() or exc.__class__.__name__
        return DiagnosticResult("Orologio di sistema", "warning", details)

    if not date_header:
        return DiagnosticResult(
            "Orologio di sistema",
            "warning",
            "Impossibile leggere l'ora dal server (header Date mancante)",
        )

    try:
        server_dt = parsedate_to_datetime(date_header)
        if server_dt is None:
            raise ValueError("Header Date non valido")
        if server_dt.tzinfo:
            server_dt = server_dt.astimezone(timezone.utc)
        else:
            server_dt = server_dt.replace(tzinfo=timezone.utc)
    except Exception:
        return DiagnosticResult(
            "Orologio di sistema",
            "warning",
            f"Header Date non valido: {date_header}",
        )

    local_dt = datetime.now(timezone.utc)
    skew_seconds = abs((local_dt - server_dt).total_seconds())
    skew_int = int(round(skew_seconds))

    if skew_seconds <= max_skew_seconds:
        return DiagnosticResult("Orologio di sistema", "ok", f"Differenza di {skew_int} secondi")

    return DiagnosticResult(
        "Orologio di sistema",
        "error",
        f"Orologio sfasato di {skew_int} secondi; sincronizza l'ora di Windows e riprova",
    )


async def run_connection_diagnostics(
    lang_code: str,
    backup_dir: Optional[Path],
) -> List[DiagnosticResult]:
    """Esegue la diagnosi completa e restituisce l'elenco dei risultati."""
    results: List[DiagnosticResult] = []

    proxies = _detect_proxy_env()
    if proxies:
        summaries = [f"{k}={v}" for k, v in proxies]
        results.append(
            DiagnosticResult(
                "Proxy di sistema",
                "info",
                "; ".join(summaries),
            )
        )
    else:
        results.append(DiagnosticResult("Proxy di sistema", "ok", "Nessuna variabile proxy attiva"))

    headers = {
        "Accept-Language": _build_accept_language(lang_code),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JWTime/diagnostic",
    }

    results.append(await _resolve_host("wol.jw.org"))
    results.append(await _doh_lookup("wol.jw.org"))
    results.append(await _udp_dns_lookup("wol.jw.org", "1.1.1.1"))
    results.append(await _udp_dns_lookup("wol.jw.org", "8.8.8.8"))
    results.append(await _tcp_latency_test("wol.jw.org"))

    normalized_lang = _request_lang_from_setting(lang_code)
    r_code, lp_code = get_route_info((lang_code or "it").lower().strip())
    localized_home = f"https://wol.jw.org/{normalized_lang}/wol/h/{r_code}/{lp_code}"
    results.append(await _https_probe(localized_home, headers))
    results.append(await _certificate_probe(localized_home, headers))
    results.append(await _system_clock_check(headers))
    results.append(await _https_probe("https://www.microsoft.com", headers, "Connessione HTTPS (Microsoft)"))
    results.extend(await _workbook_probe(lang_code))
    results.append(await _github_pack_probe(lang_code))

    if proxies:
        tested = set()
        for _, proxy_url in proxies:
            if proxy_url in tested:
                continue
            tested.add(proxy_url)
            results.append(await _proxy_probe(proxy_url, headers))

    log_dir = get_log_dir()
    results.append(_directory_write_test("Scrittura log", log_dir))

    local_state_dir = _get_local_state_dir()
    results.append(_directory_write_test("Scrittura cache locale", local_state_dir))

    if backup_dir:
        results.append(_directory_write_test("Scrittura backup", backup_dir))
        results.append(_disk_space_test(backup_dir))
    else:
        results.append(
            DiagnosticResult(
                "Scrittura backup",
                "warning",
                "BackupManager non inizializzato: impossibile verificare",
            )
        )

    return results
