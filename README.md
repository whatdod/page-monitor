# Monitoraggio pagine → notifica Teams (versione multi-pagina)

## Cosa cambia rispetto a prima

- Il vecchio `state.txt` (una sola pagina) è sostituito da una cartella
  `state/` con un file per pagina.
- Il vecchio secret `TEAMS_WEBHOOK_URL` è sostituito da un secret **per
  pagina**, es. `TEAMS_WEBHOOK_TOSCANA`.
- Ogni pagina ha il proprio flow Teams dedicato, con un messaggio fisso che
  la identifica (niente più problemi di testo dinamico).

## Migrazione dalla versione precedente

1. Su GitHub, crea un nuovo secret `TEAMS_WEBHOOK_TOSCANA` con lo stesso
   valore che aveva `TEAMS_WEBHOOK_URL` (copialo dal flow Teams esistente,
   quello già funzionante). Puoi eliminare il vecchio secret dopo.
2. Sostituisci nel repository i tre file: `check_page.py`,
   `.github/workflows/check-page.yml`.
3. Rinomina/sposta il vecchio `state.txt` in `state/bando-toscana.txt`
   (oppure lascia che venga ricreato da zero al primo giro: verrà solo
   inviato un messaggio "di inizializzazione" in più, non un problema).

## Passare da chat 1:1 a gruppo Teams

1. In Teams, apri (o crea) una chat di gruppo con la tua collega (in una
   chat 1:1 esistente: "Aggiungi persone" per farla diventare di gruppo).
2. Apri il flow Teams collegato alla pagina Toscana, sull'azione
   "Posta messaggio in una chat o canale": cambia "Posta in" da "Chat con
   il bot del flusso" a **"Chat di gruppo"**, poi seleziona il gruppo
   appena creato.
3. Se il bot non riesce a pubblicare nel gruppo (errore di permessi),
   cambia anche "Posta come" da "Bot del flusso" a **"Utente"**: il
   messaggio verrà pubblicato a nome tuo invece che del bot, ma funziona
   in qualsiasi chat di cui sei membro senza bisogno che il bot vi sia
   aggiunto.
4. Salva e testa (vedi sotto).

## Come aggiungere una nuova pagina da monitorare

1. **Teams**: duplica un flow esistente (o crea uno nuovo dal template
   "Post to a channel when a webhook request is received", vedi il primo
   README per i dettagli). Nell'azione di pubblicazione:
   - "Posta in": "Chat di gruppo" → stesso gruppo di prima.
   - Messaggio: testo fisso che indichi QUALE pagina è cambiata, es.
     "🔔 La pagina di [nome sito] è stata aggiornata! [url]".
   - Copia il nuovo URL del webhook (tab "Parametri" del trigger).
2. **GitHub secret**: Settings → Secrets and variables → Actions → New
   secret. Nome a piacere ma coerente, es. `TEAMS_WEBHOOK_NOMESITO`.
   Valore: l'URL copiato al punto 1.
3. **Workflow**: apri `.github/workflows/check-page.yml`, nella sezione
   `env` dello step "Esegui controllo pagine" aggiungi una riga come:
   ```yaml
   TEAMS_WEBHOOK_NOMESITO: ${{ secrets.TEAMS_WEBHOOK_NOMESITO }}
   ```
4. **Script**: apri `check_page.py`, nella lista `PAGES` in cima al file
   aggiungi una voce:
   ```python
   {
       "name": "Nome del sito",
       "url": "https://esempio.it/pagina-da-monitorare",
       "state_file": "state/nome-sito.txt",
       "webhook_env": "TEAMS_WEBHOOK_NOMESITO",
   },
   ```
5. Commit, poi testa lanciando manualmente il workflow da GitHub Actions.

## Come funziona il rilevamento delle modifiche

Per ogni pagina, lo script prova in ordine:
1. Il meta tag `article:modified_time` nell'HTML (il più robusto, usato da
   molti siti istituzionali basati su WordPress/simili).
2. Il testo visibile "Ultima modifica: DD.MM.YYYY".
3. Se nessuno dei due è presente: un hash dell'intera pagina, che rileva
   **qualsiasi** cambiamento nel contenuto HTML (utile per siti con
   struttura sconosciuta, ma può generare qualche falso positivo se la
   pagina contiene elementi che cambiano da soli, es. contatori visite,
   pubblicità, timestamp automatici — in tal caso serve un pattern più
   specifico, da valutare caso per caso quando si presenta il problema).

## Uso aziendale con account personali — attenzione

Questo sistema, così com'è, gira su un account GitHub e un account
cron-job.org personali. Prima di affidarci un processo di lavoro
condiviso con colleghi, vale la pena verificare con l'IT/il responsabile
se l'azienda preferisce che venga spostato su account/strumenti aziendali
— così il sistema non dipende da un singolo account personale e resta
accessibile anche se cambi ruolo o lasci l'azienda.

## Tutto il resto

Le istruzioni su cron-job.org (creazione del cronjob, token GitHub,
`repository_dispatch`) restano identiche a quelle già configurate e
funzionanti: non serve toccare nulla lì per aggiungere nuove pagine, dato
che è lo stesso identico workflow GitHub a occuparsi di tutte le pagine
nell'elenco `PAGES` ad ogni esecuzione.
