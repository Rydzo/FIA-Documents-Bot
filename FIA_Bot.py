import os
import re
import requests
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup

# --- Ustawienia środowiska / sekrety ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit("Brak TELEGRAM_BOT_TOKEN lub TELEGRAM_CHAT_ID w zmiennych środowiskowych.")
CHAT_ID = int(CHAT_ID)

# --- Konfiguracja ---
SEASON_URL = "https://www.fia.com/documents/championships/fia-formula-one-world-championship-14/season/season-2025-2071"
TIMEOUT = 25
LAST_SEEN_FILE = "last_seen.txt"
UA = {"User-Agent": "Mozilla/5.0"}


# --- Pomocnicze funkcje ------------------------------------------------------

def tg_send(text: str):
    """Wyślij wiadomość tekstową do Telegrama."""
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text},
        timeout=TIMEOUT
    )
    r.raise_for_status()


def load_last_seen() -> str:
    """Wczytaj zapamiętany adres ostatniego pliku."""
    try:
        with open(LAST_SEEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def save_last_seen(url: str):
    """Zapisz adres ostatniego pliku."""
    with open(LAST_SEEN_FILE, "w", encoding="utf-8") as f:
        f.write(url)


def normalize_url(u: str) -> str:
    """
    Normalizuje URL do porównań:
    - wymusza https,
    - usuwa query, fragment i końcowy slash,
    - obniża wielkość liter w domenie.
    """
    p = urlparse(u)
    scheme = "https"
    netloc = p.netloc.lower()
    path = p.path.rstrip("/")
    return urlunparse((scheme, netloc, path, "", "", ""))


def looks_like_event_name(text: str) -> bool:
    """Sprawdź, czy tekst wygląda na nazwę wyścigu (Grand Prix / Tests)."""
    t = (text or "").strip()
    return bool(t) and ("Grand Prix" in t or "Tests" in t)


def humanize_event_from_url(url: str) -> str:
    """
    Fallback: z URL np. 2025_azerbaijan_grand_prix -> Azerbaijan Grand Prix.
    """
    m = re.search(r"/decision-document/\d{4}_([a-z_]+)_grand_prix", url, re.I)
    if m:
        words = m.group(1).split("_")
        return " ".join(w.capitalize() for w in words) + " Grand Prix"
    return "Latest event"


def clean_title(raw: str) -> str:
    """
    Czyści i formatuje tytuł dokumentu:
    - usuwa zbędne spacje,
    - dodaje separator przed 'Published on',
    - dba o spację przed 'CET'.
    """
    t = (raw or "").strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s*Published on\s*", " | Published on ", t, flags=re.I)
    t = re.sub(r"(?i)(\d{2}:\d{2})CET", r"\1 CET", t)
    return t


def fetch_latest_pdf_from_season():
    """
    Zwraca (event_name, title, url_pdf) dla najnowszego dokumentu PDF
    z oficjalnej strony sezonu FIA.
    """
    r = requests.get(SEASON_URL, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    lis = soup.find_all("li")
    if not lis:
        return None

    for idx, li in enumerate(lis):
        a = li.find("a", href=True)
        if not a:
            continue
        href = a["href"].strip()
        if not (href.lower().endswith(".pdf") and "/system/files/decision-document/" in href):
            continue

        url_abs = href if href.startswith("http") else requests.compat.urljoin(SEASON_URL, href)
        url_abs = normalize_url(url_abs)
        title = clean_title(a.get_text(strip=True) or "FIA document")

        # Znajdź nazwę eventu w poprzednich elementach listy
        event_name = None
        for j in range(idx - 1, -1, -1):
            li_prev = lis[j]
            if not li_prev.find("a"):
                txt = li_prev.get_text(" ", strip=True)
                if looks_like_event_name(txt):
                    event_name = txt
                    break
        if not event_name:
            event_name = humanize_event_from_url(url_abs)

        return event_name, title, url_abs

    return None


# --- Główna logika ------------------------------------------------------------

if __name__ == "__main__":
    latest = fetch_latest_pdf_from_season()
    if not latest:
        tg_send("Brak nowych dokumentów FIA na stronie sezonu.")
    else:
        ev, title, url = latest
        url_norm = normalize_url(url)
        last = load_last_seen()

        if normalize_url(last) != url_norm:
            msg = (
                f"New Document FIA\n"
                f"Event: {ev}\n"
                f"Title: {title}\n"
                f"Link: {url}"
            )
            tg_send(msg)
            save_last_seen(url_norm)
        # jeśli nie ma nowego dokumentu – nic nie wysyłamy
