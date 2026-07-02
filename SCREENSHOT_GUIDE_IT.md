# Guida screenshot sito IT

Questa guida definisce la base per produrre gli screenshot italiani di JW Time 4.0 e replicarli poi nelle altre lingue con gli stessi tagli.

## Metodo

Usare sempre l'harness reale dell'app:

```powershell
.\.venv-pyside6\Scripts\python.exe scripts\run_website_screenshots.py --version v4 --languages it
```

Il comando avvia l'app in `JWTIME_SCREENSHOT_MODE=1`, usa profili `APPDATA` e `LOCALAPPDATA` isolati, forza solo le impostazioni utili allo screenshot e non modifica il comportamento normale dell'app.

Per rigenerare solo alcune immagini:

```powershell
.\.venv-pyside6\Scripts\python.exe scripts\run_website_screenshots.py --version v4 --languages it --captures media_window,media_window_annotated
```

Le coordinate e gli stati UI sono in `screenshot-fixtures/v4/manifest.json`.

Il codice che avvia l'app in modalita' screenshot e' nel repo app:

- `scripts/run_website_screenshots.py`
- `tools/website_screenshots/runner.py`

Questa modalita' si attiva solo tramite `JWTIME_SCREENSHOT_MODE=1`, impostata dallo script. L'avvio normale dell'app non usa il runner.

## Dimensioni Standard

| Tipo | Dimensione | Note |
| --- | ---: | --- |
| Finestra principale | 1244x1088 | Base per manuale e news |
| Wizard primo avvio | 680x765 | Passo iniziale del percorso guidato, alla dimensione reale minima |
| Ritagli aree finestra principale | Manifest | Coordinate identiche per tutte le lingue |
| Finestra Media | 812x2048 | Layout verticale completo |
| Ritagli Media | Manifest | Sezioni, contenuti, barra, musica |
| Pannelli inferiori | 1244x160 | Programma, Messaggio, REC |
| Popup calendario settimana | 460x380 | Contenitore interno opaco del dialogo |
| Impostazioni | 1053x1088 | Dimensione minima reale della finestra |
| Schermi 16:9 | 1004x565 | Schermo Pubblico, Contatempo, messaggi |
| Editor Schermo Contatempo | 1448x1283 | Altezza reale con livello selezionato |
| Ritagli editor | Manifest | Scene, livelli, trasformazioni |
| Monitor Web | 1236x2016 | Rendering controllato con cornice browser e URL generico |

## Scaletta Di Riferimento

La scaletta e' definita nel manifest `v4`, scenario `midweek`, settimana `2026-05-18`.
Per le altre lingue cambiano i testi, ma restano invariati ordine, durate, aree e categorie.

## Asset Generati

Creati in `images/manual/it/`:

| Area | File principali |
| --- | --- |
| Finestra principale | `schermata-principale-v4-real.png`, `schermata-principale-v4-news.png`, `schermata-principale-v4-annotata-real.png` |
| Primo avvio | `primo-avvio-guidato-v4.png` |
| Aree numerate | `area-1-titolo-orologio-v4.png` ... `area-8-modalita-v4.png`, `area-tabella-v4-real.png` |
| Media | `media-window-v4-real.png`, `media-window-v4-annotata-real.png`, `media-window-sezioni-v4.png`, `media-window-contenuti-v4.png`, `media-window-barra-v4.png`, `media-window-musica-v4-real.png` |
| Timer | `manipolazione-operazioni-v4.png`, `timer-aggiornamento-tempo-reale-v4.png`, `manipolazione-regolazione-v4.png` |
| Schermi e messaggi | `schermo-pubblico-v4.png`, `schermo-contattempo-v4.png`, `messaggio-tutto-schermo-v4.png`, `messaggio-parziale-v4.png` |
| Editor Contatempo | `personalizzazione_schermo_contatempo_base-v4.png`, `personalizzazione_schermo_contatempo_base_scena-v4.png`, `personalizzazione_schermo_contatempo_base_layout-v4.png`, `personalizzazione_schermo_contatempo_base_trasformazioni-v4.png` |
| Programma/Messaggio/REC | `navigazione-settimanale-v4.png`, `navigazione-settimanale-pannello-v4.png`, `messaggi-elenco-v4.png`, `REC-v4.png` |
| Impostazioni | `impostazioni-generale-v4.png`, `impostazioni-congregazioni-v4.png`, `impostazioni-adunanze-v4.png`, `impostazioni-schermo-v4.png`, `impostazioni-media-v4.png`, `impostazioni-zoom-v4.png`, `impostazioni-connessioni-v4.png`, `impostazioni-registrazioni-v4.png`, `impostazioni-backup-v4.png` |
| Monitor Web | `monitor-web-v4.png`, `monitor-web-editor-v4.png`, `impostazioni-connessioni-accesso-remoto-v4.png` |

## Uso Nel Manuale

`it/manual.html` ora punta agli asset `-v4` per tutte le immagini app gia' rigenerate.
Anche le immagini Monitor Web hanno asset `-v4`: non sono patch su vecchi screenshot, ma rendering controllati dal manifest con URL generico.

## Come Modificare Uno Screenshot

1. Trova l'id della cattura in `screenshot-fixtures/v4/manifest.json`.
2. Modifica solo la voce interessata: dimensione, crop, annotazioni, blur, stato UI o testo demo.
3. Rigenera solo quell'immagine con `--captures`.
4. Controlla visivamente il PNG in `images/manual/it/`.
5. Se il manuale usa gia' lo stesso nome file, non serve modificare l'HTML.

Esempi:

```powershell
.\.venv-pyside6\Scripts\python.exe scripts\run_website_screenshots.py --version v4 --languages it --captures main_window_annotated
.\.venv-pyside6\Scripts\python.exe scripts\run_website_screenshots.py --version v4 --languages it --captures monitor_web_view,monitor_web_controller
```

## Report Generati

Ogni esecuzione puo' creare file sotto `screenshot-fixtures/v4/reports/`.
Sono report temporanei utili per controllo locale, non sorgenti del sito: sono ignorati da Git.

## Regole Per Le Altre Lingue

- Stesso manifest e stesse coordinate.
- Cambiare solo `--languages`.
- Mantenere gli stessi nomi file equivalenti dentro `images/manual/<lang>/`.
- Se un testo tradotto sfora, si corregge la UI o la dimensione standard nel manifest, non il singolo screenshot manualmente.
