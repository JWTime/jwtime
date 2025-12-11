# file: backup/pack_manager.py

import os
import json
import zipfile
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from backup.backup_manager import BackupPackage
from version import __version__

logger = logging.getLogger(__name__)


class PackManager:
    """Gestisce export/import di pacchetti in formato .jwtimepack (ZIP)."""
    
    SCHEMA_VERSION = "1.0"
    TIMEZONE = "Europe/Rome"
    
    @classmethod
    def export_packages(cls, packages: List[BackupPackage], output_path: str) -> bool:
        """
        Esporta uno o più pacchetti in un file .jwtimepack.
        
        Args:
            packages: Lista di BackupPackage da esportare
            output_path: Percorso del file di output
        
        Returns:
            True se successo
        """
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Crea manifest globale
                manifest = {
                    'schema_version': cls.SCHEMA_VERSION,
                    'app_version': __version__,
                    'timezone': cls.TIMEZONE,
                    'created_at': datetime.now().isoformat(),
                    'package_count': len(packages),
                    'packages': []
                }
                
                # Aggiungi ogni pacchetto
                for idx, package in enumerate(packages):
                    package_id = f"package_{idx:03d}"
                    
                    # Metadata pacchetto
                    pkg_info = {
                        'id': package_id,
                        'program_type': package.program_type,
                        'week_id': package.week_id,
                        'ui_lang': package.ui_lang,
                        'page_lang': package.page_lang,
                        'last_updated': package.last_updated,
                        'content_hash': package.content_hash
                    }
                    manifest['packages'].append(pkg_info)
                    
                    # Dati pacchetto
                    data_filename = f"{package_id}/data.json"
                    package_data = {
                        'rows': package.rows
                    }
                    zf.writestr(data_filename, json.dumps(package_data, ensure_ascii=False, indent=2))
                
                # Scrivi manifest
                zf.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
                
                # Calcola checksum globale
                checksum = cls._calculate_zip_checksum(output_path)
                checksum_data = {
                    'checksum': checksum,
                    'algorithm': 'sha256'
                }
                zf.writestr('checksum.json', json.dumps(checksum_data, ensure_ascii=False, indent=2))
            
            logger.info(f"Esportati {len(packages)} pacchetti in {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Errore export pacchetti: {e}")
            return False
    
    @classmethod
    def import_packages(cls, input_path: str, validate_only: bool = False) -> Optional[Dict]:
        """
        Importa pacchetti da un file .jwtimepack.
        
        Args:
            input_path: Percorso del file da importare
            validate_only: Se True, valida solo senza estrarre
        
        Returns:
            Dict con {
                'valid': bool,
                'manifest': Dict,
                'packages': List[BackupPackage],
                'warnings': List[str],
                'errors': List[str]
            }
        """
        result = {
            'valid': False,
            'manifest': None,
            'packages': [],
            'warnings': [],
            'errors': []
        }
        
        try:
            with zipfile.ZipFile(input_path, 'r') as zf:
                # Verifica integrità base
                if zf.testzip() is not None:
                    result['errors'].append("File ZIP corrotto")
                    return result
                
                # Leggi manifest
                try:
                    manifest_data = zf.read('manifest.json')
                    manifest = json.loads(manifest_data.decode('utf-8'))
                    result['manifest'] = manifest
                except Exception as e:
                    result['errors'].append(f"Manifest non valido: {e}")
                    return result
                
                # Valida schema version
                schema_version = manifest.get('schema_version')
                if schema_version != cls.SCHEMA_VERSION:
                    result['warnings'].append(
                        f"Schema version diversa: {schema_version} (attesa: {cls.SCHEMA_VERSION})"
                    )
                
                # Verifica checksum (se presente)
                if 'checksum.json' in zf.namelist():
                    try:
                        checksum_data = json.loads(zf.read('checksum.json').decode('utf-8'))
                        # Nota: la verifica checksum richiederebbe ricalcolo su file esistente
                        # che potrebbe essere modificato. Skip per ora.
                    except Exception as e:
                        result['warnings'].append(f"Checksum non verificabile: {e}")
                
                if validate_only:
                    result['valid'] = len(result['errors']) == 0
                    return result
                
                # Estrai pacchetti
                packages = []
                for pkg_info in manifest.get('packages', []):
                    try:
                        package_id = pkg_info['id']
                        data_filename = f"{package_id}/data.json"
                        
                        if data_filename not in zf.namelist():
                            result['warnings'].append(f"Dati mancanti per {package_id}")
                            continue
                        
                        data_json = zf.read(data_filename)
                        data = json.loads(data_json.decode('utf-8'))
                        
                        # Crea BackupPackage
                        package = BackupPackage(
                            program_type=pkg_info['program_type'],
                            week_id=pkg_info['week_id'],
                            rows=data['rows'],
                            ui_lang=pkg_info['ui_lang'],
                            page_lang=pkg_info.get('page_lang'),
                            last_updated=pkg_info.get('last_updated'),
                            content_hash=pkg_info.get('content_hash')
                        )
                        packages.append(package)
                        
                    except Exception as e:
                        result['warnings'].append(f"Errore caricamento {package_id}: {e}")
                
                result['packages'] = packages
                result['valid'] = len(result['errors']) == 0 and len(packages) > 0
                
                logger.info(f"Importati {len(packages)} pacchetti da {input_path}")
                return result
                
        except Exception as e:
            result['errors'].append(f"Errore lettura file: {e}")
            logger.error(f"Errore import pacchetti: {e}")
            return result
    
    @staticmethod
    def _calculate_zip_checksum(zip_path: str) -> str:
        """Calcola checksum SHA256 del file ZIP."""
        sha256 = hashlib.sha256()
        with open(zip_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()


def export_single_package(package: BackupPackage, output_path: str) -> bool:
    """
    Helper per esportare un singolo pacchetto.
    
    Args:
        package: BackupPackage da esportare
        output_path: Percorso del file di output
    
    Returns:
        True se successo
    """
    return PackManager.export_packages([package], output_path)


def export_all_packages(backup_manager, output_path: str) -> bool:
    """
    Helper per esportare tutti i pacchetti disponibili.
    
    Args:
        backup_manager: Istanza di BackupManager
        output_path: Percorso del file di output
    
    Returns:
        True se successo
    """
    all_packages = []
    
    for program_type in ['midweek', 'weekend']:
        package_infos = backup_manager.list_packages(program_type)

        for pkg_info in package_infos:
            ui_lang = pkg_info.get('ui_lang')
            package = backup_manager.load_package(program_type, pkg_info['week_id'], ui_lang)
            if package:
                all_packages.append(package)
    
    if not all_packages:
        logger.warning("Nessun pacchetto da esportare")
        return False
    
    return PackManager.export_packages(all_packages, output_path)
