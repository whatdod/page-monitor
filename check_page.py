#!/usr/bin/env python3
"""
Monitora una lista di pagine web e invia una notifica a Teams (via webhook
dedicato per ciascuna pagina) quando il "segnale di modifica" di una pagina
cambia rispetto all'ultimo controllo.

Come aggiungere una nuova pagina da monitorare:
1. Crea in Teams un nuovo flow (duplica quello esistente), con un messaggio
   fisso che indica QUALE pagina è cambiata, e copia il nuovo URL webhook.
2. Su GitHub: Settings -> Secrets and variables -> Actions -> New secret.
   Dai al secret un nome tipo TEAMS_WEBHOOK_NOMESITO e incolla l'URL.
3. Aggiungi quel nome nel file .github/workflows/check-page.yml, nella
   sezione "env" dello step "Esegui controllo pagine" (segui lo schema
   delle righe già presenti).
4. Aggiungi una nuova voce nella lista PAGES qui sotto, con lo stesso nome
   di secret usato al punto 2/3.
"""

import os
import re
import sys
import json
import hashlib
import urllib.request

# ---------------------------------------------------------------------------
# Elenco delle pagine da monitorare. Aggiungi qui nuove voci quando serve.
# ---------------------------------------------------------------------------
PAGES = [
    {
        "name": "Bando Toscana",
        "url": "https://www.sviluppo.toscana.it/bando/bandirs2025/",
        "state_file": "state/bando-toscana.txt",
        "webhook_env": "TEAMS_WEBHOOK_TOSCANA",
    },
   {
      "name":"Bando MASE - amteriale di recupero",
      "url":"https://www.mase.gov.it/portale/-/bando-credito-d-imposta-materiali-di-recupero-spese-annualita-2024-imminente-apertura-dello-sportello-per-la-presentazione-delle-istanze-",
      "state_file": "state/bando-mase-materiali-recupero.txt", 
      "webhook_env": "TEAMS_WEBHOOK_MASE", },
   
    # Esempio per una prossima pagina (basta scommentare e adattare):
    # {
    #     "name": "Nome del sito",
    #     "url": "https://esempio.it/pagina",
    #     "state_file": "state/nome-sito.txt",
    #     "webhook_env": "TEAMS_WEBHOOK_NOMESITO",
    # },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

META_PATTERN = re.compile(
    r'property=["\']article:modified_time["\']\s+content=["\']([^"\']+)["\']'
)
TEXT_PATTERN = re.compile(r"Ultima modifica:\s*([0-9]{2}\.[0-9]{2}\.[0-9]{4})")


def fetch_page(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def extract_signature(html: str) -> str:
    """
    Restituisce un "segnale" testuale che rappresenta lo stato della pagina.
    Prova prima pattern noti (meta tag, testo "Ultima modifica"); se nessuno
    corrisponde, calcola un hash dell'intera pagina: rileva QUALSIASI
    cambiamento, utile per siti con struttura non ancora nota.
    """
    m = META_PATTERN.search(html)
    if m:
        return m.group(1).strip()

    m = TEXT_PATTERN.search(html)
    if m:
        return m.group(1).strip()

    return "hash:" + hashlib.sha256(html.encode("utf-8")).hexdigest()


def read_previous_state(state_file: str) -> str | None:
    if not os.path.exists(state_file):
        return None
    with open(state_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
        return content or None


def write_state(state_file: str, value: str) -> None:
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        f.write(value)


def notify_teams(webhook_url: str) -> None:
    # Il testo del messaggio è configurato come testo fisso dentro il flow
    # Teams collegato a QUESTO specifico webhook: qui basta far scattare
    # la richiesta.
    payload = {"triggered": True}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def check_page(page: dict) -> bool:
    """Controlla una singola pagina. Restituisce True se non ci sono stati errori."""
    name = page["name"]
    url = page["url"]
    state_file = page["state_file"]
    webhook_env = page["webhook_env"]

    webhook_url = os.environ.get(webhook_env)
    if not webhook_url:
        print(f"[{name}] ERRORE: variabile {webhook_env} non impostata.", file=sys.stderr)
        return False

    try:
        html = fetch_page(url)
    except Exception as e:
        print(f"[{name}] ERRORE durante il fetch: {e}", file=sys.stderr)
        return False

    new_value = extract_signature(html)
    old_value = read_previous_state(state_file)

    if old_value == new_value:
        print(f"[{name}] Nessuna modifica.")
        return True

    print(f"[{name}] Modifica rilevata: {old_value} -> {new_value}. Invio notifica Teams...")
    try:
        notify_teams(webhook_url)
    except Exception as e:
        print(f"[{name}] ERRORE durante l'invio a Teams: {e}", file=sys.stderr)
        write_state(state_file, new_value)
        return False

    write_state(state_file, new_value)
    print(f"[{name}] Fatto.")
    return True


def main() -> int:
    all_ok = True
    for page in PAGES:
        ok = check_page(page)
        all_ok = all_ok and ok
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
