# DEPLOYMENT & INFRASTRUCTURE TOPOLOGY — Kairyx Enterprise

---

## 1. Production Service Architecture

| Service | Technology | Hosting | Production URL / Endpoint |
|---|---|---|---|
| **Bot & Polling** | `aiogram 3.x` | Railway | `@Ka1ryx_bot` |
| **REST API Server** | `aiohttp.web` (Python 3.13) | Railway (`web: python bot.py`) | `https://amorix-bot-production.up.railway.app` |
| **Frontend WebApp** | SPA (Vanilla HTML5 / CSS3 / JS) | GitHub Pages & Railway Static | `https://akuma7277.github.io/amorix-bot/webapp/index.html` |
| **Database** | PostgreSQL (Async SQLAlchemy 2.0) | Railway Managed Postgres | `DATABASE_URL` (with SQLite memory fallback for tests) |

---

## 2. Health & Verification Checkpoints

```bash
# 1. API Health Check
curl -i https://amorix-bot-production.up.railway.app/health
# Response: HTTP 200 OK {"status": "ok"}

# 2. Database Connection Check
curl -i https://amorix-bot-production.up.railway.app/health/ready
# Response: HTTP 200 OK {"status": "ready", "database": "connected"}

# 3. Frontend SPA Accessibility Check
curl -I https://akuma7277.github.io/amorix-bot/webapp/index.html
# Response: HTTP 200 OK
```
