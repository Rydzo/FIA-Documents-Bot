# FIA Telegram Bot

A **Python** bot that **monitors the FIA website** for documents of the **2025 Formula 1 season**  
and **sends the newest PDF to Telegram as soon as it is published**.

The project was prepared with the assistance of **ChatGPT (OpenAI)**.

---

## Features

- Monitors the 2025 Formula 1 season page on [fia.com](https://www.fia.com/documents/championships/fia-formula-one-world-championship-14/season/season-2025-2071).
- Sends to Telegram **only the newest PDF document** (e.g., stewards’ decisions, classifications).
- Stores the last sent file in `last_seen.txt` to avoid duplicate notifications.
- Can run continuously in the background (via cron/Task Scheduler).

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR-USER/fia-telegram-bot.git
   cd fia-telegram-bot
   ```
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

1. **Create a bot on Telegram** using [@BotFather](https://t.me/BotFather) and copy the `HTTP API token`.
2. **Get your chat_id** (for example via [@userinfobot](https://t.me/userinfobot)).
3. **Set environment variables** (recommended for security):
   - **Linux / macOS (bash/zsh):**
     ```bash
     export TELEGRAM_BOT_TOKEN="your_token"
     export TELEGRAM_CHAT_ID="your_chat_id"
     ```
   - **Windows (CMD/PowerShell – for the current session):**
     ```cmd
     set TELEGRAM_BOT_TOKEN=your_token
     set TELEGRAM_CHAT_ID=your_chat_id
     ```

> Your token and chat_id are not stored in the repository.

---

## Running the Bot

Manual check:
```bash
python FIA_Bot.py
```
If a new FIA document has been published, the bot will send a Telegram message in the format:

```
NEW FIA document
Event: [Grand Prix name]
[document title]
[link_to_file.pdf]
```

---

## Automatic Execution

- **Linux (cron)** – check every 5 minutes:
  ```bash
  */5 * * * * /usr/bin/python3 /full/path/FIA_Bot.py
  ```
- **Windows (Task Scheduler)**  
  Create a task running:
  ```cmd
  py C:\full\path\FIA_Bot.py
  ```

This way the bot runs in the background and will notify you immediately when the FIA publishes a new document.

---

## Repository Files

| File                | Description                                               |
|---------------------|-----------------------------------------------------------|
| **FIA_Bot.py**      | Main bot script.                                          |
| **requirements.txt**| List of Python libraries (`requests`, `beautifulsoup4`).  |
| **.gitignore**      | Ignored files (`last_seen.txt`, Python cache, `.env`).    |
| **README.md**       | This description and setup guide.                         |

---

## How It Works

1. The bot fetches the FIA 2025 season page.
2. Finds the **most recent PDF document**.
3. Checks whether the link differs from the one stored in `last_seen.txt`.
4. If it’s new – **sends a message to Telegram** and updates `last_seen.txt`.
5. If no new document is found – exits without sending anything.

---

## License

This project is provided for educational and personal use.  
The author is not affiliated with the FIA or Formula 1.

---

## Acknowledgements

- [FIA](https://www.fia.com/) – for providing public access to race documents.
- **ChatGPT (OpenAI)** – for assistance in creating and refining the code and documentation.