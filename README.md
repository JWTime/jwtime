# Manuale JW Time

Questa cartella contiene il nuovo sito statico del manuale di JW Time App.

## Struttura

- `assets/` – risorse condivise (CSS, immagini, PDF, eventuale JS).
- `index.html` – pagina di ingresso con selezione lingua.
- `it/` – versione italiana del manuale (`index.html`).
- `en/`, `es/`, ecc. – crea una cartella per ogni lingua futura.

## Aggiornare i contenuti

1. Modifica i file HTML o le risorse nella cartella `website/`.
2. Per mantenere coerenza, riusa il CSS globale e crea solo gli elementi nuovi necessari.
3. Se aggiungi una lingua copia `it/index.html`, rinominalo e traduci i testi.

## Caricamento su GitHub

Se non usi ancora Git da riga di comando puoi:

1. Aprire il repository su GitHub.
2. Navigare nella cartella `website/` e cliccare **Add file → Upload files**.
3. Selezionare i file aggiornati dal tuo PC e confermare con un messaggio di commit (es. “Aggiorna manuale IT”).
4. Ripetere ogni volta che apporti modifiche locali.

Più avanti potrai spostarti a un flusso Git completo (`git add`, `git commit`, `git push`), ma questo metodo è sufficiente per iniziare.
