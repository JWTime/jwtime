# file: backup/background_updater.py

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QSettings

from data_extraction.midweek import MidweekDataExtraction
from data_extraction.weekend import WeekendDataExtraction
from backup.backup_manager import BackupManager, BackupPackage, get_iso_week_id

logger = logging.getLogger(__name__)


class BackgroundUpdater(QObject):
    """
    Gestisce l'aggiornamento in background dei pacchetti di backup.
    
    Caratteristiche:
    - Throttling: micro-slot di lavoro con pause per non bloccare UI
    - Priorità: le azioni utente cancellano immediatamente il background
    - Debounce rete: attende stabilità prima di considerare online
    - Backoff progressivo sugli errori
    - Trigger: 15 minuti dopo l'avvio app (no più daily update alle 04:00)
    """
    
    # Segnali
    update_started = pyqtSignal()
    update_progress = pyqtSignal(str, str)  # (program_type, week_id)
    update_completed = pyqtSignal(str, str, bool)  # (program_type, week_id, success)
    all_updates_completed = pyqtSignal()
    
    # Costanti temporali (in secondi)
    SLOT_WORK_DURATION = 0.4  # 400ms di lavoro
    SLOT_PAUSE_DURATION = 1.5  # 1.5s di pausa
    INTER_WEEK_DELAY = 0.25  # 250ms tra settimane
    NETWORK_DEBOUNCE = 20  # 20s per considerare rete stabile
    
    # Backoff progressivo
    BACKOFF_LEVELS = [600, 1800, 7200]  # 10min, 30min, 2h
    
    def __init__(self, backup_manager: BackupManager, parent=None):
        super().__init__(parent)
        self.backup_manager = backup_manager
        self.settings = QSettings("NomeOrganizzazione", "JWTimeApp")
        
        # Stato
        self.is_running = False
        self.is_enabled = False
        self.cancel_requested = False
        self.user_action_in_progress = False
        
        # Errori e backoff
        self.error_count = 0
        self.last_error_time = None
        self.backoff_until = None
        
        # Timer periodici
        self.daily_timer = QTimer(self)
        self.daily_timer.timeout.connect(self._on_daily_trigger)
        
        self.post_load_timer = QTimer(self)
        self.post_load_timer.setSingleShot(True)
        self.post_load_timer.timeout.connect(self._on_post_load_trigger)
        
        # Rete
        self.network_online = True
        self.network_stable_since = time.time()
    
    def enable(self, enabled: bool = True):
        """Abilita/disabilita gli aggiornamenti in background."""
        self.is_enabled = enabled
        
        if enabled:
            # NON scheduliamo più il daily update alle 04:00
            # Usiamo solo il timer di avvio (15 minuti dopo l'apertura app)
            logger.info("Background updater abilitato (trigger: 15min dopo avvio)")
        else:
            self.daily_timer.stop()
            self.cancel()
            logger.info("Background updater disabilitato")
    
    def set_user_action_in_progress(self, in_progress: bool):
        """
        Notifica che un'azione utente è in corso (caricamento esplicito).
        Cancella immediatamente il job background se attivo.
        """
        self.user_action_in_progress = in_progress
        
        if in_progress and self.is_running:
            logger.info("Azione utente rilevata: cancellazione job background")
            self.cancel()
    
    def cancel(self):
        """Richiede la cancellazione del job corrente."""
        if self.is_running:
            self.cancel_requested = True
            logger.debug("Cancellazione job background richiesta")
    
    def notify_network_status(self, online: bool):
        """
        Notifica lo stato della rete.
        
        Args:
            online: True se online, False se offline
        """
        prev_online = self.network_online
        self.network_online = online
        
        if online and not prev_online:
            # Passaggio offline → online: debounce
            self.network_stable_since = time.time()
            logger.info("Rete tornata online: debounce in corso")
        elif online and prev_online:
            # Resta online: verifica se stabile
            if time.time() - self.network_stable_since >= self.NETWORK_DEBOUNCE:
                # Rete stabile: avvia sync rapido se abilitato
                if self.is_enabled and not self.is_running and not self.user_action_in_progress:
                    logger.info("Rete stabile: avvio sync rapido")
                    self.schedule_update(delay_seconds=2)
    
    def notify_load_completed(self, program_type: str):
        """
        Notifica che un caricamento utente è completato con successo.
        Schedula un mini-giro dopo 10-30s per "cogliere dati caldi".
        """
        if self.is_enabled and not self.is_running:
            delay = 15  # 15 secondi
            logger.info(f"Caricamento {program_type} completato: scheduling mini-giro tra {delay}s")
            self.post_load_timer.start(delay * 1000)
    
    def schedule_update(self, delay_seconds: int = 0):
        """
        Schedula un aggiornamento completo.
        
        Args:
            delay_seconds: Ritardo prima dell'avvio
        """
        if not self.is_enabled:
            return
        
        if delay_seconds > 0:
            QTimer.singleShot(delay_seconds * 1000, self._start_update_job)
        else:
            self._start_update_job()
    
    def _schedule_daily_update(self):
        """Schedula l'aggiornamento giornaliero alle 04:00."""
        now = datetime.now()
        target_time = now.replace(hour=4, minute=0, second=0, microsecond=0)
        
        if target_time <= now:
            # Se siamo già oltre le 04:00 oggi, schedula per domani
            target_time += timedelta(days=1)
        
        delay_seconds = (target_time - now).total_seconds()
        
        # Usa QTimer per il trigger giornaliero
        self.daily_timer.start(int(delay_seconds * 1000))
        logger.info(f"Prossimo aggiornamento giornaliero: {target_time.strftime('%Y-%m-%d %H:%M')}")
    
    def _on_daily_trigger(self):
        """Handler per il trigger giornaliero."""
        self.daily_timer.stop()
        
        if self.is_enabled and not self.user_action_in_progress:
            logger.info("Trigger giornaliero: avvio aggiornamento completo")
            self._start_update_job()
        
        # Ri-schedula per domani
        self._schedule_daily_update()
    
    def _on_post_load_trigger(self):
        """Handler per mini-giro post-caricamento utente."""
        if self.is_enabled and not self.user_action_in_progress and not self.is_running:
            logger.info("Post-load trigger: avvio mini-giro")
            self._start_update_job()
    
    def _start_update_job(self):
        """Avvia il job di aggiornamento."""
        if self.is_running:
            logger.debug("Job già in esecuzione, skip")
            return
        
        if self.user_action_in_progress:
            logger.debug("Azione utente in corso, skip")
            return
        
        # Verifica backoff
        if self.backoff_until and time.time() < self.backoff_until:
            logger.debug("In backoff, skip")
            return
        
        # Verifica rete stabile
        if not self.network_online:
            logger.debug("Rete offline, skip")
            return
        
        if time.time() - self.network_stable_since < self.NETWORK_DEBOUNCE:
            logger.debug("Rete non ancora stabile, skip")
            return
        
        # Avvia job
        self.is_running = True
        self.cancel_requested = False
        self.update_started.emit()
        
        # Esegui in modo asincrono
        asyncio.ensure_future(self._run_update_job())
    
    async def _run_update_job(self):
        """Esegue il job di aggiornamento completo."""
        try:
            logger.info("=== Background update job STARTED ===")
            
            # Determina quali tipi aggiornare (rispetta impostazioni utente)
            update_midweek = self.settings.value("backup_auto_update_midweek", True, type=bool)
            update_weekend = self.settings.value("backup_auto_update_weekend", True, type=bool)
            
            # LOG CRITICO: mostra i flag letti
            logger.info(f"FLAG LETTI DA QSETTINGS: midweek={update_midweek}, weekend={update_weekend}")
            
            types_to_update = []
            if update_midweek:
                types_to_update.append('midweek')
            if update_weekend:
                types_to_update.append('weekend')
            
            if not types_to_update:
                logger.info("Nessun tipo selezionato per l'aggiornamento")
                return
            
            # Leggi numero settimane da scaricare (rispetta impostazioni utente)
            num_weeks = self.settings.value("backup_download_weeks", 4, type=int)
            ui_lang = self.settings.value("language", "en")
            
            logger.info(f"Background update: {len(types_to_update)} tipi, {num_weeks} settimane, batch_size=4 (paralleli)")

            for program_type in types_to_update:
                if self.cancel_requested:
                    logger.info("Cancellazione richiesta, interruzione job")
                    break

                logger.info(f">>> Inizio download {program_type} per {num_weeks} settimane")

                # Crea lista di task da scaricare (filtra quelli da skippare)
                tasks_to_download = []
                for week_offset in range(num_weeks):
                    week_id = get_iso_week_id(week_offset)

                    # Verifica se già esiste e se è recente
                    existing_info = self.backup_manager.get_package_info(program_type, week_id)
                    if existing_info:
                        # Verifica se aggiornato di recente (< 24h fa)
                        last_updated = datetime.fromisoformat(existing_info['last_updated'])
                        age_hours = (datetime.now() - last_updated).total_seconds() / 3600

                        if age_hours < 24:
                            logger.debug(f"Skip {program_type} {week_id}: aggiornato {age_hours:.1f}h fa")
                            # Emetti signal completamento (skipped = success)
                            self.update_progress.emit(program_type, week_id)
                            self.update_completed.emit(program_type, week_id, True)
                            continue

                    tasks_to_download.append((program_type, week_offset, ui_lang))

                # Download in parallelo con batch_size=4
                batch_size = 4
                logger.info(f"    {len(tasks_to_download)} pacchetti da scaricare (batch_size={batch_size})")

                for i in range(0, len(tasks_to_download), batch_size):
                    if self.cancel_requested:
                        break

                    batch = tasks_to_download[i:i+batch_size]
                    logger.info(f"    Batch {i//batch_size + 1}: scarico {len(batch)} pacchetti in parallelo...")

                    # Scarica batch in parallelo
                    batch_tasks = [
                        self._download_and_save(task[0], task[1], task[2])
                        for task in batch
                    ]
                    results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                    # Processa risultati
                    for j, (task, result) in enumerate(zip(batch, results)):
                        if isinstance(result, Exception):
                            logger.error(f"Eccezione durante download {task[0]} week {task[1]}: {result}")
                            self.error_count += 1
                        elif result:
                            self.error_count = 0  # Reset errori su successo
                        else:
                            self.error_count += 1

                    # Pausa tra batch (solo se non è l'ultimo batch)
                    if not self.cancel_requested and (i + batch_size < len(tasks_to_download)):
                        logger.debug(f"    Pausa {self.INTER_WEEK_DELAY}s tra batch...")
                        await asyncio.sleep(self.INTER_WEEK_DELAY)
            
            # Applica backoff se ci sono stati errori
            if self.error_count > 0:
                backoff_level = min(self.error_count - 1, len(self.BACKOFF_LEVELS) - 1)
                backoff_seconds = self.BACKOFF_LEVELS[backoff_level]
                self.backoff_until = time.time() + backoff_seconds
                logger.warning(f"Errori rilevati: backoff per {backoff_seconds}s")
            
            logger.info("=== Background update job COMPLETED ===")
            self.all_updates_completed.emit()
            
        except Exception as e:
            logger.exception(f"Errore nel job di aggiornamento: {e}")
        finally:
            self.is_running = False
            self.cancel_requested = False
    
    async def _download_and_save(self, program_type: str, week_offset: int, ui_lang: str) -> bool:
        """
        Scarica e salva un pacchetto.
        
        Returns:
            True se successo, False se errore
        """
        week_id = get_iso_week_id(week_offset)
        
        try:
            self.update_progress.emit(program_type, week_id)
            logger.info(f"Downloading {program_type} {week_id}")
            
            # Micro-slot: lavora per SLOT_WORK_DURATION
            start_time = time.time()
            
            # Crea extractor
            if program_type == 'midweek':
                extractor = MidweekDataExtraction(
                    settimana_offset=week_offset,
                    lang_code=ui_lang
                )
            else:
                extractor = WeekendDataExtraction(
                    settimana_offset=week_offset,
                    lang_code=ui_lang
                )
            
            # Estrai dati
            rows = await extractor.estrai_dati()
            
            if not rows:
                logger.warning(f"Nessun dato estratto per {program_type} {week_id}")
                self.update_completed.emit(program_type, week_id, False)
                return False
            
            # Crea pacchetto
            package = BackupPackage(
                program_type=program_type,
                week_id=week_id,
                rows=rows,
                ui_lang=ui_lang,
                page_lang=ui_lang  # Potremmo rilevarlo dall'extractor se disponibile
            )
            
            # Salva con swap atomico
            success = self.backup_manager.save_package(package, replace_if_exists=True)
            
            if success:
                logger.info(f"[OK] Pacchetto salvato: {program_type} {week_id}")
            
            self.update_completed.emit(program_type, week_id, success)
            
            # Pausa post-slot
            elapsed = time.time() - start_time
            if elapsed < self.SLOT_WORK_DURATION:
                await asyncio.sleep(self.SLOT_WORK_DURATION - elapsed)
            
            # Pausa tra slot
            await asyncio.sleep(self.SLOT_PAUSE_DURATION)
            
            return success
            
        except asyncio.CancelledError:
            logger.info(f"Download cancellato per {program_type} {week_id}")
            self.update_completed.emit(program_type, week_id, False)
            return False
        except Exception as e:
            logger.error(f"Errore download {program_type} {week_id}: {e}")
            self.update_completed.emit(program_type, week_id, False)
            return False


def schedule_first_update(updater: BackgroundUpdater, delay_seconds: int = 50):
    """
    Schedula il primo aggiornamento all'avvio dell'app.
    
    Args:
        updater: Istanza del BackgroundUpdater
        delay_seconds: Ritardo in secondi (default 50s)
    """
    if updater.is_enabled:
        logger.info(f"Scheduling primo aggiornamento tra {delay_seconds}s")
        updater.schedule_update(delay_seconds)
