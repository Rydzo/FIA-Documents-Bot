import os
import re
import requests
from urllib.parse import urlparse, urlunparse
from bs4 import BeautifulSoup

# --- Secrets from ENV (GitHub Actions / local) ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
if not BOT_TOKEN or not CHAT_ID:
    raise SystemExit("Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID env vars.")
CHAT_ID = int(CHAT_ID)

# --- Config ---
SEASON_URL = "https://www.fia.com/documents/championships/fia-formula-one-world-championship-14/season/season-2025-2071"
TIMEOUT = 25
LAST_SEEN_FILE = "last_seen.txt"
UA = {"User-Agent": "Mozilla/5.0"}

# ----------------------- Telegram -----------------------

def tg_send(text: str):
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text},
        timeout=TIMEOUT
    )
    r.raise_for_status()

# ----------------------- State -----------------------

def load_last_seen() -> str:
    try:
        with open(LAST_SEEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last_seen(url: str):
    with open(LAST_SEEN_FILE, "w", encoding="utf-8") as f:
        f.write(url)

# ----------------------- Utils -----------------------

def normalize_url(u: str) -> str:
    """
    Normalize URL for comparisons:
    - force https,
    - drop query/fragment and trailing slash,
    - lowercase host.
    """
    p = urlparse(u)
    scheme = "https"
    netloc = p.netloc.lower()
    path = p.path.rstrip("/")
    return urlunparse((scheme, netloc, path, "", "", ""))

def looks_like_event_name(text: str) -> bool:
    t = (text or "").strip()
    return bool(t) and ("Grand Prix" in t or "Tests" in t)

def humanize_event_from_url(url: str) -> str:
    # e.g. .../decision-document/2025_azerbaijan_grand_prix_... -> Azerbaijan Grand Prix
    m = re.search(r"/decision-document/\d{4}_([a-z_]+)_grand_prix", url, re.I)
    if m:
        words = m.group(1).split("_")
        return " ".join(w.capitalize() for w in words) + " Grand Prix"
    return "Latest event"

def clean_title(raw: str) -> str:
    t = (raw or "").strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s*Published on\s*", " | Published on ", t, flags=re.I)
    t = re.sub(r"(?i)(\d{2}:\d{2})CET", r"\1 CET", t)
    return t

# ----------------------- Core -----------------------

def fetch_latest_pdf_from_season():
    """
    Return (event_name, title, url_pdf) for the newest PDF on the FIA season page.
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

        # find event header by scanning previous <li> without <a>
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

# ----------------------- Main -----------------------

if __name__ == "__main__":
    latest = fetch_latest_pdf_from_season()
    if not latest:
        # ensure state file exists so repo/Actions always has it
        save_last_seen(load_last_seen())
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
        else:
            # nothing new; still make sure
