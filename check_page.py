#!/usr/bin/env python3
"""
Monitora la pagina del bando e invia una notifica a Teams quando
la data di "Ultima modifica" cambia.

Variabili d'ambiente richieste (impostate come GitHub Secrets):
- TEAMS_WEBHOOK_URL : URL del webhook creato con l'app "Workflows" di Teams

Stato persistito nel file state.txt, che viene committato nel repo
dal workflow di GitHub Actions dopo ogni esecuzione.
"""

import os
import re
import sys
import json
import urllib.request

PAGE_URL = "https://www.sviluppo.toscana.it/bando/bandirs2025/"
STATE_FILE = "state.txt"

# User-Agent "normale" per evitare blocchi anti-bot banali
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch_page(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def extract_last_modified(html: str) -> str | None:
    """
    Prova prima il meta tag article:modified_time (più stabile),
    poi fa fallback sul testo visibile "Ultima modifica: DD.MM.YYYY".
    """
    m = re.search(
        r'property=["\']article:modified_time["\']\s+content=["\']([^"\']+)["\']',
        html,
    )
    if m:
        return m.group(1).strip()

    m = re.search(r"Ultima modifica:\s*([0-9]{2}\.[0-9]{2}\.[0-9]{4})", html)
    if m:
        return m.group(1).strip()

    return None


def read_previous_state() -> str | None:
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        return content or None


def write_state(value: str) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(value)


def notify_teams(webhook_url: str) -> None:
    # Il messaggio mostrato in Teams è ora testo fisso configurato
    # direttamente nel flow di Power Automate. Qui basta inviare
    # una richiesta POST qualsiasi per farlo scattare.
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


def main() -> int:
    webhook_url = os.environ.get("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        print("ERRORE: variabile TEAMS_WEBHOOK_URL non impostata.", file=sys.stderr)
        return 1

    try:
        html = fetch_page(PAGE_URL)
    except Exception as e:
        print(f"ERRORE durante il fetch della pagina: {e}", file=sys.stderr)
        return 1

    new_value = extract_last_modified(html)
    if new_value is None:
        print("ERRORE: non ho trovato la data di ultima modifica nella pagina.", file=sys.stderr)
        return 1

    old_value = read_previous_state()

    if old_value == new_value:
        print(f"Nessuna modifica. Data invariata: {new_value}")
        return 0

    print(f"Modifica rilevata: {old_value} -> {new_value}. Invio notifica Teams...")
    try:
        notify_teams(webhook_url)
    except Exception as e:
        print(f"ERRORE durante l'invio a Teams: {e}", file=sys.stderr)
        # Anche se la notifica fallisce, aggiorno lo stato per non
        # riprovare all'infinito con lo stesso valore vecchio già noto.
        write_state(new_value)
        return 1

    write_state(new_value)
    print("Fatto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
