import os, re, requests
from bs4 import BeautifulSoup

# --- ENV (w Actions/sekrety lub lokalnie) ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")
if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit("Brak TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID w zmiennych środowiskowych.")
CHAT_ID = int(CHAT_ID)

# --- Konfiguracja ---
SEASON_URL = "https://www.fia.com/documents/championships/fia-formula-one-world-championship-14/season/season-2025-2071"
TIMEOUT = 25
ONLY_STEWARDS = False
LAST_SEEN_FILE = "last_seen.txt"
UA = {"User-Agent": "Mozilla/5.0"}

def tg_send(text: str):
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text},
        timeout=TIMEOUT
    )
    r.raise_for_status()

def load_last_seen():
    try:
        with open(LAST_SEEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last_seen(url: str):
    with open(LAST_SEEN_FILE, "w", encoding="utf-8") as f:
        f.write(url)

def looks_like_event_name(text: str) -> bool:
    t = (text or "").strip()
    return bool(t) and ("Grand Prix" in t or "Tests" in t)

def humanize_event_from_url(url: str) -> str:
    """
    Fallback: z URL-a /decision-document/2025_azerbaijan_grand_prix_... -> 'Azerbaijan Grand Prix'
    """
    m = re.search(r"/decision-document/\d{4}_([a-z_]+)_grand_prix", url, re.I)
    if m:
        words = m.group(1).split("_")
        return " ".join(w.capitalize() for w in words) + " Grand Prix"
    return "Latest event"

def clean_title(raw: str) -> str:
    """
    Popraw odstępy, rozdziel 'Published on...' itp.
    """
    t = (raw or "").strip()
    t = re.sub(r"\s+", " ", t)  # zredukuj wielokrotne spacje
    t = re.sub(r"\s*Published on", " | Published on", t, flags=re.I)
    t = t.replace("CET", " CET")  # brakująca spacja bywa w źródle
    return t

def fetch_latest_pdf_from_season():
    """
    Zwraca (event_name, title, url_pdf) najnowszego dokumentu PDF ze strony sezonu 2025.
    Szuka pierwszego <a href="...pdf">; event ustala z najbliższego poprzedniego <li> bez linka,
    a jeśli się nie uda — używa fallbacku z URL.
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

        # URL absolutny
        url = href if href.startswith("http") else requests.compat.urljoin(SEASON_URL, href)
        title = clean_title(a.get_text(strip=True) or "FIA document")
        if ONLY_STEWARDS and not re.search(r"(Decision|The Stewards)", title, re.I):
            continue

        # Szukamy nazwy eventu cofając się do poprzednich <li> bez <a>
        event_name = None
        for j in range(idx - 1, -1, -1):
            li_prev = lis[j]
            if not li_prev.find("a"):  # kandydat na nagłówek eventu
                txt = li_prev.get_text(" ", strip=True)
                if looks_like_event_name(txt):
                    event_name = txt
                    break
        if not event_name:
            event_name = humanize_event_from_url(url)

        return (event_name, title, url)

    return None

if __name__ == "__main__":
    latest = fetch_latest_pdf_from_season()
    if not latest:
        tg_send("Brak PDF-ów do pobrania na stronie sezonu.")
    else:
        ev, title, url = latest
        last = load_last_seen()
        if url != last:
            msg = f"NOWY dokument FIA\nEvent: {ev}\nTytuł: {title}\nLink: {url}"
            tg_send(msg)
            save_last_seen(url)
        # jeśli nic nowego – milczymy
