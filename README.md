# FIA Telegram Bot

Bot w języku **Python**, który **monitoruje stronę FIA** z dokumentami sezonu **2025 Formuły 1**  
i **wysyła na Telegrama najnowszy plik PDF natychmiast po jego publikacji**.

Projekt został przygotowany przy wsparciu **ChatGPT (OpenAI)**.

---

## Funkcje

- Śledzi stronę sezonu 2025 Formuły 1 na [fia.com](https://www.fia.com/documents/championships/fia-formula-one-world-championship-14/season/season-2025-2071).
- Wysyła na Telegram link **tylko do najnowszego dokumentu PDF** (np. decyzji sędziów, klasyfikacji).
- Zapamiętuje ostatni wysłany plik w `last_seen.txt`, aby nie powtarzać powiadomień.
- Może działać w tle w trybie ciągłym (cron/Harmonogram zadań).

---

## Instalacja

1. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/TWOJ-USER/fia-telegram-bot.git
   cd fia-telegram-bot
   ```
2. Zainstaluj wymagania:
   ```bash
   pip install -r requirements.txt
   ```

---

## Konfiguracja

1. **Utwórz bota w Telegramie** za pomocą [@BotFather](https://t.me/BotFather) i skopiuj `HTTP API token`.
2. **Ustal swój chat_id** (np. botem [@userinfobot](https://t.me/userinfobot)).
3. **Ustaw zmienne środowiskowe** (rekomendowane – bezpieczne):
   - **Linux / macOS (bash/zsh):**
     ```bash
     export TELEGRAM_BOT_TOKEN="twój_token"
     export TELEGRAM_CHAT_ID="twój_chat_id"
     ```
   - **Windows (CMD/PowerShell – na czas sesji):**
     ```cmd
     set TELEGRAM_BOT_TOKEN=twój_token
     set TELEGRAM_CHAT_ID=twój_chat_id
     ```

> Token i chat_id nie są przechowywane w repozytorium.

---

## Uruchomienie

Ręczne sprawdzenie:
```bash
python FIA_Bot.py
```
Jeśli pojawił się nowy dokument FIA, bot wyśle na Telegram wiadomość w formacie:

```
NOWY dokument FIA
Event: [nazwa Grand Prix]
[tytuł dokumentu]
[link_do_pliku.pdf]
```

---

## Automatyczne uruchamianie

- **Linux (cron)** – sprawdzanie co 5 minut:
  ```bash
  */5 * * * * /usr/bin/python3 /pełna/ścieżka/FIA_Bot.py
  ```
- **Windows (Harmonogram zadań)**  
  Utwórz zadanie wywołujące:
  ```cmd
  py C:\pełna\ścieżka\FIA_Bot.py
  ```

Dzięki temu bot będzie działał w tle i powiadomi Cię natychmiast, gdy FIA opublikuje nowy dokument.

---

## Pliki w repozytorium

| Plik              | Opis                                                       |
|-------------------|------------------------------------------------------------|
| **FIA_Bot.py**         | Główny skrypt bota.                                        |
| **requirements.txt** | Lista bibliotek Pythona (`requests`, `beautifulsoup4`). |
| **.gitignore**    | Ignorowane pliki (`last_seen.txt`, cache Pythona, `.env`). |
| **README.md**     | Ten plik z opisem i instrukcją.                             |

---

## Działanie krok po kroku

1. Bot pobiera stronę sezonu 2025 z FIA.
2. Znajduje **najświeższy plik PDF**.
3. Sprawdza, czy link do tego pliku różni się od zapisanego w `last_seen.txt`.
4. Jeśli jest nowy – **wysyła wiadomość na Telegram** i aktualizuje `last_seen.txt`.
5. Jeśli nie ma nowego dokumentu – kończy działanie bez wysyłania.

---

## Licencja

Projekt udostępniony do dowolnego użytku edukacyjnego i prywatnego.  
Autor nie jest w żaden sposób powiązany z FIA ani z Formułą 1.

---

## Podziękowania

- [FIA](https://www.fia.com/) – za publiczny dostęp do dokumentów wyścigowych.
- **ChatGPT (OpenAI)** – pomoc w stworzeniu i udoskonaleniu kodu oraz dokumentacji.
