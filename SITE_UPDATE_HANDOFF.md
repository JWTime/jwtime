# Handoff aggiornamento sito JW Time 4.0

Documento da usare in una nuova chat per aggiornare il sito statico JW Time.

## Contesto

- Repo sito: `c:\Users\stefa\Desktop\Contatempo\JW_Time_App\website`
- Branch sito controllato: `main`
- Il sito e' un repo Git separato dentro la cartella `website`.
- L'app attiva e' nel ramo `release/pyside6`, ma nel testo pubblico del sito non citare PyQt, PySide o dettagli di framework.
- Obiettivo editoriale: spiegare il valore pratico per l'utente rispetto alla versione Store ufficiale precedente.
- Target pagina principale novita: `news.html` nelle lingue `it`, `en`, `es`, `de`, `fr`, `pt_BR`.
- Pagina richiamata dall'app: `https://jwtime.github.io/jwtime/<lang>/news.html`.
- Le vecchie versioni dell'app usano ancora `communications.html`; oggi quelle pagine reindirizzano a `news.html`. Tenerle funzionanti.

## Stato attuale del sito

Nel sito esiste gia' una bozza 4.0 in:

- `it/news.html`
- `en/news.html`
- `es/news.html`
- `de/news.html`
- `fr/news.html`
- `pt_BR/news.html`

La bozza copre gia':

- Schermo Contatempo personalizzabile.
- Gestione Congregazioni.
- Controllo remoto da Server Web.
- Interfaccia rinnovata.
- Impostazioni piu' chiare.
- Registrazione piu' flessibile.
- Miglioramenti generali.

Pero' mancano molte novita importanti gia' implementate nell'app, soprattutto:

- finestra Media completa;
- media ufficiali, cache offline, pacchetti e controllo media;
- Schermo Pubblico;
- import playlist/JWPlaylist/JWLPlaylist;
- gruppi media, riordino e gestione manuale;
- avvio guidato;
- profili congregazione piu' dettagliati;
- protezioni PIN e QR del Server Web;
- stabilita finestre/schermi/monitor;
- miglioramenti registrazione/audio piu' concreti;
- nuova finestra Novita nell'app.

Nota sulle pagine manuale:

- `it/manual.html` ha gia' una preview "Versione 4.0.0".
- `en/manual.html`, `es/manual.html`, `de/manual.html`, `fr/manual.html`, `pt_BR/manual.html` risultano ancora orientate a "Versione 2.1.0" nella preview iniziale. Vanno allineate.

## Fonte contenuti gia' sintetizzata nell'app

L'app contiene un riepilogo interno in:

- `../resources/release_notes/current.json`

Quel file e' una buona base breve, ma per il sito serve una versione piu' estesa, con sezioni, esempi d'uso e immagini.

Messaggio breve usato dall'app:

> Novita importanti in JW Time: media integrati, profili congregazione, controllo remoto e nuovo Contatempo.

Sintesi:

> Questa versione raccoglie molte novita pensate per rendere piu' semplice preparare l'adunanza, gestire piu' congregazioni e controllare timer, media e schermi con meno passaggi.

## Linea editoriale

Scrivere sempre dal punto di vista dell'utente:

- dire "nuova finestra Media", non "nuovo backend";
- dire "piu' stabile quando si cambia monitor", non "correzione geometrie Qt";
- dire "profili congregazione separati", non "payload QSettings";
- dire "controllo remoto protetto", non "servizi auth";
- dire "pagina Novita nell'app", non "release_notes JSON".

Evitare:

- riferimenti a PyQt5, PySide6, Qt, framework, refactor, branch o migrazioni;
- promesse troppo assolute tipo "mai piu' errori";
- dettagli tecnici interni se non aiutano l'utente.

Usare tono:

- concreto;
- ordinato;
- rassicurante ma non pubblicitario;
- utile per chi prepara o gestisce l'adunanza.

## Aggiornamenti consigliati al sito

### 1. `news.html` in tutte le lingue

Aggiornare l'articolo 4.0 rendendolo la fonte completa delle novita.

Titolo consigliato:

- IT: `Versione 4.0.0`
- EN: `Version 4.0.0`
- ES: `Version 4.0.0`
- DE: `Version 4.0.0`
- FR: `Version 4.0.0`
- PT-BR: `Versao 4.0.0`

Il sito va preparato come release gia' pubblicata: non usare formule future.

Sottotitolo consigliato IT:

> Media integrati, profili congregazione, nuovo Contatempo personalizzabile, Schermo Pubblico, controllo remoto e un'interfaccia piu' chiara per preparare e gestire l'adunanza con meno passaggi.

Struttura consigliata:

1. In breve
2. Media e preparazione dell'adunanza
3. Schermo Contatempo e Schermo Pubblico
4. Congregazioni, profili e backup
5. Server Web e controllo remoto
6. Registrazione e audio
7. Impostazioni, avvio guidato e interfaccia
8. Miglioramenti di stabilita

### 2. `manual.html` in tutte le lingue

Allineare la preview "Ultime Novita" / "Latest News" a 4.0.

La preview non deve duplicare tutto `news.html`; deve solo spingere alla pagina novita.

Contenuto breve consigliato IT:

- Finestra Media per immagini, cantici, video e playlist.
- Profili congregazione con impostazioni separate.
- Schermo Contatempo personalizzabile e nuovo Schermo Pubblico.
- Controllo remoto da browser con QR e protezioni.
- Impostazioni riorganizzate e configurazione iniziale guidata.

### 3. `communications.html`

Le pagine `communications.html` reindirizzano gia' a `news.html`. Tenerle, per compatibilita con versioni vecchie dell'app.

Verificare che ogni lingua contenga ancora:

- redirect a `news.html`;
- testo breve coerente con la pagina news;
- eventuale commento `jwtime-message-id` se viene ancora letto da versioni precedenti.

Formato storico documentato nel repo app:

- `../Documenti/COMMUNICATIONS_ONLINE_FORMAT.md`

### 4. Home page `index.html`

Valutare se aggiornare la sezione feature/hero per menzionare le novita piu' visibili:

- Media integrati;
- Schermo Contatempo personalizzabile;
- profili congregazione;
- controllo remoto da browser;
- Schermo Pubblico.

Non serve trasformare la home in una pagina changelog: bastano 2-4 richiami.

### 5. Immagini

Esistono gia':

- `images/manual/<lang>/news_3_0.png`
- screenshot manuale per schermata principale, impostazioni, connessioni, backup, registrazioni, ecc.

Aggiornamenti immagini consigliati:

- screenshot finestra Media;
- screenshot Controllo Media;
- screenshot profili/congregazioni;
- screenshot editor layout Contatempo;
- screenshot Schermo Pubblico/editor pubblico;
- screenshot QR Server Web / accesso remoto;
- screenshot nuova finestra Novita nell'app, se utile.

Se non ci sono screenshot definitivi, mantenere temporaneamente l'immagine `news_3_0.png` ma togliere o aggiornare la nota "screenshot in aggiornamento" quando disponibile.

## Contenuto esteso consigliato per `news.html` IT

### Introduzione

Con la versione 4.0.0, JW Time diventa piu' completo nella preparazione e nella gestione dell'adunanza. Le novita principali riguardano i media, i profili congregazione, la visualizzazione sugli schermi, il controllo remoto e una configurazione piu' guidata.

L'obiettivo e' ridurre i passaggi manuali: raccogliere i contenuti necessari, controllare cosa manca, usare impostazioni diverse per congregazioni diverse e intervenire durante l'adunanza con piu' rapidita.

### Novita principali

- Nuova finestra Media: immagini, cantici, video, PDF, URL e contenuti della settimana sono raccolti in un unico posto.
- Media ufficiali e offline: JW Time puo' scaricare, verificare e riusare contenuti ufficiali gia' disponibili in locale.
- Schermo Contatempo personalizzabile: preset, layout modificabili, colori, sfondi, logo, orologio e disposizione degli elementi.
- Schermo Pubblico: uscita separata per media, immagini, PDF, video e contenuti visivi.
- Profili congregazione: ogni congregazione puo' mantenere impostazioni, finestre, schermi, lingua, server, registrazione e layout separati.
- Server Web potenziato: accesso tramite QR, controlli remoti per programma/timer e protezioni con PIN.
- Interfaccia rinnovata: impostazioni piu' ordinate, tema chiaro/scuro e configurazione iniziale guidata.

### Media e preparazione dell'adunanza

Scrivere una sezione forte: e' una delle novita piu' grandi.

Punti da includere:

- finestra Media organizzata per sezioni della scaletta;
- importazione di file locali, URL e playlist;
- supporto JWPlaylist/JWLPlaylist dove disponibile;
- gruppi media manuali e riordino;
- anteprima immagini/PDF con zoom, pan, cambio pagina e posizioni salvate;
- cantici ufficiali con cache locale e aggiornamenti;
- musica pre-adunanza e post-adunanza/sottofondo;
- pacchetti media "Solo locali" e "Tutti offline";
- Controllo Media con riepilogo problemi e dettagli copiabili.

Testo breve possibile:

> La nuova finestra Media aiuta a preparare in anticipo tutto cio' che serve per la settimana. Puoi raccogliere immagini, cantici, video, PDF, URL e playlist, controllare quali contenuti sono disponibili, individuare eventuali file mancanti e usare i media direttamente sullo Schermo Pubblico.

### Schermo Contatempo e Schermo Pubblico

Punti da includere:

- Contatempo non piu' fisso: layout personalizzabili;
- preset di partenza;
- editor visuale;
- gestione colori, sfondi, logo, orologio e testi;
- finestra libera o schermo intero;
- migliore gestione monitor;
- Schermo Pubblico separato per media e contenuti visuali;
- scene prima/durante/dopo adunanza;
- scrittura dell'anno e logo.

Testo breve possibile:

> Il Contatempo puo' essere adattato meglio al proprio contesto: si parte da preset pronti e si puo' intervenire su disposizione, colori e contenuti. Accanto al Contatempo, lo Schermo Pubblico permette di mostrare media e contenuti visuali su un'uscita separata, con una gestione piu' stabile durante l'adunanza.

### Congregazioni, profili e backup

Punti da includere:

- piu' congregazioni nello stesso JW Time;
- ogni profilo conserva impostazioni proprie;
- import/export/duplicazione profili;
- auto-selezione congregazione in base alla prossima adunanza;
- migrazione impostazioni esistenti;
- backup piu' completi.

Testo breve possibile:

> Se JW Time viene usato in contesti diversi, i profili congregazione evitano di riconfigurare ogni volta l'app. Ogni congregazione puo' mantenere le proprie preferenze, i propri schermi, la propria lingua, i propri layout e le proprie impostazioni operative.

### Server Web e controllo remoto

Punti da includere:

- QR per aprire il Server Web da telefono/tablet;
- controllo remoto di programma e timer;
- stato remoto piu' chiaro;
- PIN separati dove disponibili;
- accesso locale e, dove configurato, accesso remoto/tunnel.

Testo breve possibile:

> Il Server Web non serve solo a visualizzare informazioni da browser: ora puo' diventare un vero punto di controllo remoto per alcune operazioni dell'app, utile quando si lavora da un altro dispositivo nella stessa rete.

### Registrazione e audio

Punti da includere:

- registrazione piu' flessibile;
- pausa e ripresa;
- modalita per parte o file unico dove configurata;
- gestione dispositivi audio;
- opzioni piu' chiare nelle impostazioni;
- migliore integrazione con timer/media.

### Impostazioni, avvio guidato e interfaccia

Punti da includere:

- interfaccia rinnovata;
- impostazioni divise meglio per area;
- nuova configurazione iniziale;
- tema chiaro/scuro/automatico;
- scala interfaccia;
- lingua interfaccia e lingua programmi;
- finestre e popup con stile coerente;
- nuova finestra Novita dentro l'app, richiamabile dal banner.

### Miglioramenti e correzioni

Raggruppare senza fare una lista troppo tecnica:

- gestione piu' stabile dei monitor;
- finestre ricordate meglio per congregazione;
- meno problemi con finestre fuori schermo;
- chiusura app piu' ordinata;
- download programmi/media piu' resilienti;
- cache media piu' controllata;
- meno stati incoerenti durante cambio settimana, lingua, congregazione o programma.

## Checklist per la chat che aggiorna il sito

- [ ] Prima controllare `git status` nel repo `website`.
- [ ] Aggiornare `it/news.html` per primo.
- [ ] Portare la stessa struttura in `en`, `es`, `de`, `fr`, `pt_BR`.
- [ ] Aggiornare le preview news in tutti i `manual.html`.
- [ ] Verificare `communications.html` in tutte le lingue.
- [ ] Valutare aggiornamento home `index.html` in tutte le lingue.
- [ ] Non modificare `Manuale.psd` salvo richiesta esplicita.
- [ ] Non citare PyQt/PySide/Qt o branch di sviluppo.
- [ ] Usare testi user-facing e concreti.
- [ ] Controllare link relativi tra lingue.
- [ ] Aprire almeno `it/news.html` e una lingua estera per controllo visivo.
- [ ] Fare `git diff --check` nel repo `website`.

## Prompt pronto per nuova chat

```text
Siamo nel repo sito statico JW Time:
c:\Users\stefa\Desktop\Contatempo\JW_Time_App\website

Il sito e' un repository Git separato. Prima controlla `git status`.

Devi aggiornare il sito alla versione 4.0.0 di JW Time usando come guida:
- SITE_UPDATE_HANDOFF.md
- le pagine attuali `*/news.html`
- le preview `*/manual.html`
- opzionalmente `../resources/release_notes/current.json`

Obiettivo: aggiornare la pagina Novita e i richiami nel manuale/home con tutte le novita realmente implementate, scritte dal punto di vista dell'utente. Non citare PyQt, PySide, Qt, branch o dettagli interni. Raggruppa le novita in modo leggibile: Media, Contatempo/Schermo Pubblico, Congregazioni, Server Web, Registrazione, Impostazioni, Stabilita.

Lavora prima su `it/news.html`, poi replica/adatta nelle altre lingue `en`, `es`, `de`, `fr`, `pt_BR`. Mantieni la struttura HTML e lo stile esistenti. Aggiorna anche la preview "Ultime Novita" nei `manual.html` delle varie lingue, perche alcune sono ancora ferme alla versione 2.1.0.

Non modificare `Manuale.psd`. Non fare refactor CSS non necessario. Al termine esegui `git diff --check` nel repo sito e riepiloga i file cambiati.
```
