# Manuale JW Time

Questa cartella contiene il sito statico multilingue e il manuale di JW Time.

La versione pubblicata descritta dal sito è JW Time 4.2.2.

Prima di pubblicare, verifica le pagine di rilascio e i metadati letti dall'app:

```powershell
python scripts/audit_site_release.py
```

Per ogni nuova versione vanno aggiornati, in tutte le lingue, la pagina
principale, la comunicazione letta dall'app, la pagina delle novità e il
manuale. Nel manuale devono avanzare sia la voce nell'indice sia il badge
della versione, e il riepilogo iniziale deve includere le correzioni e le
novità del rilascio. L'audit controlla anche questi elementi per evitare che
una pagina resti visivamente riferita alla versione precedente.

Per le note storiche sull'aggiornamento alla versione 4.0, vedi:

- [`SITE_UPDATE_HANDOFF.md`](SITE_UPDATE_HANDOFF.md)
