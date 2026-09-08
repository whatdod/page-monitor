# Monitoraggio pagina bando → notifica Teams

Sistema gratuito, senza server e senza consumo di token AI: uno script Python
gira ogni 15 minuti su GitHub Actions e avvisa un canale Teams quando cambia
la data di "Ultima modifica" della pagina del bando.

## 1. Crea il webhook su Teams (app Workflows)

I vecchi "Incoming Webhook" di Teams sono stati ritirati da Microsoft: oggi
si usa l'app **Workflows**, integrata gratuitamente in Teams.

1. Nel canale Teams dove vuoi ricevere le notifiche, clicca sui **tre puntini (...)**
   accanto al nome del canale → **Workflows**.
2. Cerca il template **"Post to a channel when a webhook request is received"**
   (in italiano: "Registra nel canale quando viene ricevuta una richiesta webhook").
3. Conferma team e canale, poi crea il flow.
4. Copia l'**URL del webhook** che ti viene mostrato: lo userai al punto 3.

> Nota: il flow creato in automatico dal template posta genericamente il campo
> di testo che riceve. Se vuoi personalizzare come appare il messaggio, apri il
> flow in Power Automate ed edita l'azione "Post message in a chat or channel",
> usando il contenuto dinamico proveniente dal corpo della richiesta (il campo
> `text` che lo script invia).

## 2. Crea un repository GitHub (gratuito)

1. Vai su github.com, crea un nuovo repository (può essere privato).
2. Carica in questo repository i 3 file di questo pacchetto, mantenendo la
   struttura delle cartelle:
   - `check_page.py`
   - `.github/workflows/check-page.yml`
   - `README.md` (questo file, opzionale)

## 3. Configura il secret con l'URL del webhook

1. Nel repository: **Settings → Secrets and variables → Actions → New repository secret**.
2. Nome: `TEAMS_WEBHOOK_URL`
3. Valore: l'URL copiato al punto 1.
4. Salva.

## 4. Attiva e testa

1. Vai nella tab **Actions** del repository.
2. Se richiesto, abilita i workflow ("I understand my workflows, go ahead and enable them").
3. Apri il workflow **"Monitora pagina bando"** e clicca **Run workflow** per
   testarlo manualmente subito (invece di aspettare i 15 minuti).
4. La prima esecuzione registra la data corrente e ti manda un messaggio di
   "monitoraggio avviato" — è normale, serve solo a inizializzare lo stato.
   Dalla seconda esecuzione in poi arriverà una notifica solo se la data
   di "Ultima modifica" è effettivamente cambiata.

Da quel momento in poi il controllo gira in automatico ogni 15 minuti, gratis,
senza bisogno di lasciare accesi PC o server.

## Note

- **Costi**: GitHub Actions è gratuito fino a 2.000 minuti/mese sui repo privati
  (illimitato sui repo pubblici). Con un controllo ogni 15 minuti (~96 volte
  al giorno, pochi secondi ciascuno) si resta ben sotto quella soglia.
- **Nessun token AI**: lo script fa solo un fetch HTTP e un confronto testuale,
  nessuna chiamata a modelli di intelligenza artificiale.
- **Affidabilità del cron**: GitHub non garantisce la precisione al minuto sui
  cron job (può ritardare di qualche minuto nei momenti di carico sui server
  condivisi), ma per questo scopo non è un problema.
- Se in futuro Sviluppo Toscana cambia la struttura della pagina, la funzione
  `extract_last_modified` nello script potrebbe dover essere aggiornata.
