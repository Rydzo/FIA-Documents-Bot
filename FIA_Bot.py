# id.py — wysyła TYLKO najnowszy PDF z sezonu 2025 i tylko, gdy pojawi się nowy
import os, re, requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

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
    if os.path.exists(LAST_SEEN_FILE):
        with open(LAST_SEEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def save_last_seen(url: str):
    with open(LAST_SEEN_FILE, "w", encoding="utf-8") as f:
        f.write(url)

def looks_like_event_name(text: str) -> bool:
    t = (text or "").strip()
    return bool(t) and ("Grand Prix" in t or "Tests" in t)

def fetch_latest_pdf_from_season():
    """
    1) Zbiera WSZYSTKIE <li> ze strony sezonu w kolejności.
    2) Znajduje PIERWSZY link do PDF (…/system/files/decision-document/*.pdf) = najnowszy dokument.
    3) Cofając się po poprzednich <li> szuka nazwy eventu (linia bez linków z 'Grand Prix'/'Tests').
    Zwraca: (event_name, title, pdf_url) lub None gdy brak.
    """
    r = requests.get(SEASON_URL, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    lis = soup.find_all("li")
    if not lis:
        return None

    # znajdź pierwszy PDF (to będzie najnowszy)
    for idx, li in enumerate(lis):
        a = li.find("a", href=True)
        if not a:
            continue
        href = a["href"].strip()
        if href.lower().endswith(".pdf") and "/system/files/decision-document/" in href:
            url = href if href.startswith("http") else requests.compat.urljoin(SEASON_URL, href)
            title = a.get_text(strip=True) or "FIA document"
            if ONLY_STEWARDS and not re.search(r"(Decision|The Stewards)", title, re.I):
                continue

            # cofnij się do najbliższego wcześniejszego <li> wyglądającego na nazwę eventu
            event_name = "Latest event"
            for j in range(idx - 1, -1, -1):
                li_prev = lis[j]
                # nazwa eventu zwykle nie ma <a>
                if not li_prev.find("a"):
                    txt = li_prev.get_text(" ", strip=True)
                    if looks_like_event_name(txt):
                        event_name = txt
                        break

            return (event_name, title, url)

    return None

if __name__ == "__main__":
    try:
        latest = fetch_latest_pdf_from_season()
        if not latest:
            tg_send("Brak PDF-ów do pobrania na stronie sezonu.")
        else:
            ev, title, url = latest
            last = load_last_seen()
            if url != last:
                tg_send(f"NOWY dokument FIA\nEvent: {ev}\n{title}\n{url}")
                save_last_seen(url)
            # jeśli taki sam jak ostatnio — nic nie wysyłamy
    except Exception as e:
        try:
            tg_send(f"❌ Błąd: {e}")
        finally:
            raise
