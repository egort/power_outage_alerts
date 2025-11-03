# 🔌 Power Outage Alerts

Telegram bot that monitors the **Elektrodistribucija Srbije (EDS)** website and sends alerts about **scheduled power outages** for selected areas.

---

## 🧩 Features
- Parses EDS website for new outage announcements  
- Detects updates and avoids duplicate alerts  
- Sends messages to a Telegram chat or channel  
- Configured entirely via `.env` file  
- Runs locally or in Docker / Docker Compose  
- Supports cron-like periodic checks  

---

## ⚙️ Environment Variables (`.env`)
```env
TELEGRAM_BOT_TOKEN=123456789:ABCDEF...
TELEGRAM_CHAT_ID=-1001234567890
TZ=Europe/Belgrade

# Optional filters
CITY=Subotica
STREET="Proleterskih Brigada"
```

---

## 🚀 Run Locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python parser.py
```

---

## 🐳 Run in Docker
### Build and start
```bash
docker compose up -d --build
```

### Logs
```bash
docker compose logs -f
```

### Update
```bash
git pull && docker compose up -d --build
```

---

## 📦 Structure
```
power_outage_alerts/
├─ parser.py              # main script (scraper + Telegram notifier)
├─ requirements.txt       # dependencies
├─ Dockerfile             # container build
├─ docker-compose.yaml    # deployment config
├─ .env.example           # sample env file
└─ .gitignore
```

---

## 🧠 Notes
- `.env` is injected automatically by Docker Compose.  
- All timestamps use the `TZ` timezone variable.  
- No local database — duplicate filtering is handled in-memory (or via hash file if added).  
- Designed for cron-based or daemonized operation (via Compose).  

---

## 🪪 License
MIT © [egort](https://github.com/egort)
