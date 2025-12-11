"""
Modulo per la gestione della versione dell'applicazione JW Time.
Legge automaticamente il numero di versione da:
1. version.txt (creato dallo script di build - priorità massima)
2. app.manifest (fallback legacy - versione fissa 1.0.0.0)
"""
import os, re
import sys
import xml.etree.ElementTree as ET


def get_version():
    """
    Legge il numero di versione dell'applicazione.

    Priorità:
    1. version.txt - Creato dallo script di build con la versione del task VSCode
    2. app.manifest - Fallback con versione fissa (non più aggiornata automaticamente)

    Returns:
        str: Il numero di versione nel formato 'X.Y.Z' (es. '1.9.0')
             Se non riesce a leggere, ritorna 'Unknown'
    """
    try:
        # Determina il percorso base (funziona sia in dev che con PyInstaller)
        try:
            base_path = sys._MEIPASS  # Quando impacchettato con PyInstaller
        except AttributeError:
            base_path = os.path.dirname(os.path.abspath(__file__))  # In sviluppo
        
        # Sorgente 1: version.txt (sovrascrive il manifest, impostata dallo script di build)
        ver_txt_path = os.path.join(base_path, 'version.txt')
        if os.path.exists(ver_txt_path):
            try:
                with open(ver_txt_path, 'r', encoding='utf-8') as f:
                    v = f.read().strip()
                if re.match(r'^\d+\.\d+\.\d+$', v):
                    return v
            except Exception:
                pass

        # Sorgente 2: app.manifest
        manifest_path = os.path.join(base_path, 'app.manifest')

        if not os.path.exists(manifest_path):
            return 'Unknown'
        
        # Parsing del file XML
        tree = ET.parse(manifest_path)
        root = tree.getroot()
        
        # Namespace per il parsing XML
        namespace = {'asm': 'urn:schemas-microsoft-com:asm.v1'}
        
        # Cerca il tag assemblyIdentity
        assembly_identity = root.find('asm:assemblyIdentity', namespace)
        
        if assembly_identity is not None:
            version_full = assembly_identity.get('version', 'Unknown')
            # Mostra sempre solo le prime 3 parti (X.Y.Z)
            parts = version_full.split('.')
            if len(parts) >= 3:
                return '.'.join(parts[:3])
            return version_full
        
        return 'Unknown'

    except Exception:
        return 'Unknown'


# Variabile globale con la versione dell'applicazione
__version__ = get_version()


if __name__ == '__main__':
    pass
