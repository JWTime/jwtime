# file: backup/backup_manager.py

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from threading import RLock
from PyQt5.QtCore import QSettings

logger = logging.getLogger(__name__)


class BackupPackage:
    """Rappresenta un singolo pacchetto di backup per una settimana."""
    
    def __init__(self, program_type: str, week_id: str, rows: List[Tuple],
                 ui_lang: str, page_lang: Optional[str] = None,
                 last_updated: Optional[str] = None, content_hash: Optional[str] = None):
        self.program_type = program_type  # "midweek" | "weekend"
        self.week_id = week_id  # YYYY-WW formato ISO
        self.rows = rows  # Lista di tuple (tipo, contenuto, durata)
        self.ui_lang = ui_lang
        self.page_lang = page_lang
        self.last_updated = last_updated or datetime.now().isoformat()
        self.content_hash = content_hash or self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Calcola hash del contenuto per rilevare cambiamenti."""
        content_str = json.dumps(self.rows, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        """Converte in dizionario serializzabile."""
        return {
            'program_type': self.program_type,
            'week_id': self.week_id,
            'rows': self.rows,
            'ui_lang': self.ui_lang,
            'page_lang': self.page_lang,
            'last_updated': self.last_updated,
            'content_hash': self.content_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BackupPackage':
        """Crea istanza da dizionario."""
        return cls(
            program_type=data['program_type'],
            week_id=data['week_id'],
            rows=data['rows'],
            ui_lang=data['ui_lang'],
            page_lang=data.get('page_lang'),
            last_updated=data.get('last_updated'),
            content_hash=data.get('content_hash')
        )


class BackupManager:
    """Gestisce i pacchetti di backup offline per le scalette."""

    # Rimosso limite fisso MAX_PACKAGES_PER_TYPE
    # I pacchetti vecchi vengono rimossi automaticamente in base alla data

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Inizializza il manager.

        Args:
            storage_dir: Directory per i pacchetti. Se None, usa directory cache app.
        """
        if storage_dir is None:
            # Usa directory cache di QSettings
            settings = QSettings("NomeOrganizzazione", "JWTimeApp")
            app_data_dir = Path(settings.fileName()).parent
            storage_dir = app_data_dir / "schedule_backups"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Lock per proteggere accesso concorrente all'indice
        # RLock permette allo stesso thread di acquisire il lock più volte
        self._lock = RLock()

        # File indice per metadata
        self.index_file = self.storage_dir / "index.json"
        self._load_index()

        # Pulizia automatica dei pacchetti vecchi all'avvio
        self.clean_old_packages()

        # Pulizia file orfani (file sul disco non presenti nell'indice)
        self.clean_orphaned_files()
    
    def _load_index(self):
        """Carica l'indice dei pacchetti (thread-safe)."""
        with self._lock:
            if self.index_file.exists():
                try:
                    with open(self.index_file, 'r', encoding='utf-8') as f:
                        self.index = json.load(f)
                except Exception as e:
                    logger.error(f"Errore caricamento indice: {e}")
                    self.index = {'midweek': [], 'weekend': []}
            else:
                self.index = {'midweek': [], 'weekend': []}
    
    def _save_index(self):
        """Salva l'indice dei pacchetti (thread-safe)."""
        with self._lock:
            try:
                with open(self.index_file, 'w', encoding='utf-8') as f:
                    json.dump(self.index, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Errore salvataggio indice: {e}")
    
    def save_package(self, package: BackupPackage, replace_if_exists: bool = True) -> bool:
        """
        Salva un pacchetto con swap atomico.
        
        Args:
            package: Pacchetto da salvare
            replace_if_exists: Se True, sostituisce pacchetto esistente con stesso week_id
        
        Returns:
            True se salvataggio riuscito
        """
        try:
            # Ricarica l'indice da disco per evitare overwrite da istanze stale
            self._load_index()

            # File temporaneo per swap atomico (include lingua nel nome)
            package_file = self._get_package_filename(package.program_type, package.week_id, package.ui_lang)
            temp_file = package_file.with_suffix('.tmp')
            
            # Scrivi su file temporaneo
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(package.to_dict(), f, ensure_ascii=False, indent=2)
            
            # Swap atomico
            if package_file.exists() and not replace_if_exists:
                temp_file.unlink()
                return False
            
            temp_file.replace(package_file)
            
            # Aggiorna indice
            self._update_index(package)

            logger.info(f"Pacchetto salvato: {package.program_type} {package.week_id} ({package.ui_lang})")
            return True
            
        except Exception as e:
            logger.error(f"Errore salvataggio pacchetto: {e}")
            return False
    
    def _get_package_filename(self, program_type: str, week_id: str, ui_lang: str = None) -> Path:
        """Genera il nome file per un pacchetto, includendo la lingua se specificata."""
        if ui_lang:
            return self.storage_dir / f"{program_type}_{week_id}_{ui_lang}.json"
        else:
            # Retrocompatibilità: cerca file senza lingua
            return self.storage_dir / f"{program_type}_{week_id}.json"
    
    def _update_index(self, package: BackupPackage):
        """Aggiorna l'indice con il pacchetto (thread-safe)."""
        with self._lock:
            program_type = package.program_type

            # Rimuovi entry esistente per stessa combinazione week_id + ui_lang
            # Questo permette di mantenere lingue diverse della stessa settimana
            self.index[program_type] = [
                p for p in self.index[program_type]
                if not (p['week_id'] == package.week_id and p['ui_lang'] == package.ui_lang)
            ]

            # Aggiungi nuovo entry
            self.index[program_type].append({
                'week_id': package.week_id,
                'ui_lang': package.ui_lang,
                'page_lang': package.page_lang,
                'last_updated': package.last_updated,
                'content_hash': package.content_hash
            })

            # Ordina per week_id (dal più recente)
            self.index[program_type].sort(key=lambda x: x['week_id'], reverse=True)

            # _save_index() ri-acquisirà il lock (RLock permette questo)
            self._save_index()
    
    def clean_old_packages(self):
        """Rimuove i pacchetti che si riferiscono a settimane passate (precedenti a quella corrente) (thread-safe)."""
        from datetime import datetime

        current_week_id = get_iso_week_id(0)  # Settimana corrente

        with self._lock:
            for program_type in ['midweek', 'weekend']:
                packages = self.index.get(program_type, []).copy()

                for pkg_info in packages:
                    week_id = pkg_info['week_id']

                    # Rimuovi se week_id < current_week_id (settimana passata)
                    if week_id < current_week_id:
                        ui_lang = pkg_info.get('ui_lang')
                        pkg_file = self._get_package_filename(program_type, week_id, ui_lang)

                        try:
                            if pkg_file.exists():
                                pkg_file.unlink()
                                logger.info(f"Pulizia automatica: rimosso pacchetto vecchio {program_type} {week_id} ({ui_lang})")
                        except Exception as e:
                            logger.error(f"Errore rimozione pacchetto vecchio: {e}")

                        # Rimuovi da indice
                        self.index[program_type] = [
                            p for p in self.index[program_type]
                            if not (p['week_id'] == week_id and p.get('ui_lang') == ui_lang)
                        ]

            # _save_index() ri-acquisirà il lock (RLock permette questo)
            self._save_index()
            logger.info("Pulizia pacchetti vecchi completata")
    
    def load_package(self, program_type: str, week_id: str, ui_lang: str = None) -> Optional[BackupPackage]:
        """
        Carica un pacchetto specifico.

        Args:
            program_type: "midweek" o "weekend"
            week_id: YYYY-WW
            ui_lang: Lingua UI (opzionale, per retrocompatibilità)

        Returns:
            BackupPackage se trovato, None altrimenti
        """
        try:
            package_file = self._get_package_filename(program_type, week_id, ui_lang)

            if not package_file.exists():
                # Retrocompatibilità: prova senza lingua
                if ui_lang:
                    package_file = self._get_package_filename(program_type, week_id, None)
                    if not package_file.exists():
                        return None
                else:
                    return None

            with open(package_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return BackupPackage.from_dict(data)

        except Exception as e:
            logger.error(f"Errore caricamento pacchetto {program_type} {week_id}: {e}")
            return None
    
    def get_package_info(self, program_type: str, week_id: str) -> Optional[Dict]:
        """
        Ottiene metadati di un pacchetto senza caricarlo completamente.
        
        Returns:
            Dict con metadati o None
        """
        packages = self.index.get(program_type, [])
        for pkg in packages:
            if pkg['week_id'] == week_id:
                return pkg
        return None
    
    def list_packages(self, program_type: Optional[str] = None) -> List[Dict]:
        """
        Elenca i pacchetti disponibili.
        
        Args:
            program_type: Se specificato, filtra per tipo. None = tutti.
        
        Returns:
            Lista di dizionari con metadati pacchetti
        """
        if program_type:
            return self.index.get(program_type, []).copy()
        else:
            all_packages = []
            for ptype in ['midweek', 'weekend']:
                for pkg in self.index.get(ptype, []):
                    pkg_copy = pkg.copy()
                    pkg_copy['program_type'] = ptype
                    all_packages.append(pkg_copy)
            
            # Ordina per week_id (dal più recente)
            all_packages.sort(key=lambda x: x['week_id'], reverse=True)
            return all_packages
    
    def delete_package(self, program_type: str, week_id: str, ui_lang: str = None) -> bool:
        """
        Elimina un pacchetto (thread-safe).

        Args:
            program_type: "midweek" o "weekend"
            week_id: YYYY-WW
            ui_lang: Lingua UI (opzionale, per retrocompatibilità)

        Returns:
            True se eliminato con successo
        """
        try:
            with self._lock:
                # Ricarica l'indice da disco per evitare di sovrascrivere modifiche recenti
                # _load_index() ri-acquisirà il lock (RLock permette questo)
                self._load_index()

                package_file = self._get_package_filename(program_type, week_id, ui_lang)

                if package_file.exists():
                    package_file.unlink()
                else:
                    # Se la lingua non è specificata, prova a rimuovere tutti i file di quella settimana (tutte le lingue)
                    if ui_lang is None:
                        try:
                            # Rimuovi file con lingua e senza lingua (retrocompatibilità)
                            for f in self.storage_dir.glob(f"{program_type}_{week_id}_*.json"):
                                f.unlink()
                            legacy_file = self.storage_dir / f"{program_type}_{week_id}.json"
                            if legacy_file.exists():
                                legacy_file.unlink()
                        except Exception as e:
                            logger.error(f"Errore rimozione file pacchetti per {program_type} {week_id}: {e}")

                # Rimuovi da indice (solo quella combinazione week_id + ui_lang)
                if ui_lang:
                    self.index[program_type] = [
                        p for p in self.index[program_type]
                        if not (p['week_id'] == week_id and p.get('ui_lang') == ui_lang)
                    ]
                else:
                    # Retrocompatibilità: rimuovi tutti con quel week_id
                    self.index[program_type] = [
                        p for p in self.index[program_type]
                        if p['week_id'] != week_id
                    ]

                # _save_index() ri-acquisirà il lock (RLock permette questo)
                self._save_index()

                logger.info(f"Pacchetto eliminato: {program_type} {week_id} ({ui_lang})")
                return True

        except Exception as e:
            logger.error(f"Errore eliminazione pacchetto: {e}")
            return False
    
    def clear_all_packages(self, program_type: Optional[str] = None):
        """
        Elimina tutti i pacchetti.

        Args:
            program_type: Se specificato, elimina solo quel tipo. None = tutti.
        """
        # Ricarica l'indice da disco per avere stato aggiornato
        self._load_index()

        types_to_clear = [program_type] if program_type else ['midweek', 'weekend']

        for ptype in types_to_clear:
            packages = self.index.get(ptype, []).copy()

            for pkg_info in packages:
                # Passa anche la lingua UI per eliminare il file corretto
                self.delete_package(ptype, pkg_info['week_id'], pkg_info.get('ui_lang'))

    def clean_orphaned_files(self):
        """
        Rimuove file di backup orfani (file sul disco che non sono nell'indice).
        Questo include file del formato vecchio (senza lingua nel nome) e file
        che sono stati rimossi dall'indice ma sono ancora sul disco.
        """
        with self._lock:
            try:
                # Ottieni tutti i file di backup nella directory
                all_files = list(self.storage_dir.glob("*.json"))

                # Filtra solo i file di backup (escludi index.json)
                backup_files = [f for f in all_files if f.name != "index.json"]

                # Crea un set di file che dovrebbero esistere secondo l'indice
                indexed_files = set()
                for program_type in ['midweek', 'weekend']:
                    for pkg_info in self.index.get(program_type, []):
                        week_id = pkg_info['week_id']
                        ui_lang = pkg_info.get('ui_lang')
                        filename = self._get_package_filename(program_type, week_id, ui_lang)
                        indexed_files.add(filename)

                # Rimuovi file che non sono nell'indice
                for file_path in backup_files:
                    if file_path not in indexed_files:
                        try:
                            file_path.unlink()
                            logger.info(f"Rimosso file orfano: {file_path.name}")
                        except Exception as e:
                            logger.error(f"Errore rimozione file orfano {file_path.name}: {e}")

            except Exception as e:
                logger.error(f"Errore durante pulizia file orfani: {e}")


def get_iso_week_id(offset_weeks: int = 0) -> str:
    """
    Ottiene il week_id ISO (YYYY-WW) per una data.
    
    Args:
        offset_weeks: Offset in settimane dalla settimana corrente
    
    Returns:
        Stringa nel formato YYYY-WW
    """
    target_date = datetime.now() + timedelta(weeks=offset_weeks)
    year, week, _ = target_date.isocalendar()
    return f"{year:04d}-{week:02d}"


def get_week_start_date(week_id: str) -> datetime:
    """
    Ottiene la data di inizio settimana (lunedì) da un week_id.
    
    Args:
        week_id: Stringa nel formato YYYY-WW
    
    Returns:
        datetime del lunedì di quella settimana
    """
    year, week = map(int, week_id.split('-'))
    # ISO week 1 è la settimana che contiene il primo giovedì dell'anno
    jan4 = datetime(year, 1, 4)
    week_start = jan4 - timedelta(days=jan4.isocalendar()[2] - 1)
    target_week_start = week_start + timedelta(weeks=week - 1)
    return target_week_start
