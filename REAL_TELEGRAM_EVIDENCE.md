# REAL TELEGRAM EVIDENCE & LIVE DIAGNOSTIC AUDIT (`REAL_TELEGRAM_EVIDENCE.md`)

---

## 1. Proven URLs & Bot Configuration

| Parameter | Proven Production Value | Source / Evidence |
|---|---|---|
| **Bot Username** | `@Ka1ryx_bot` | Telegram Bot Configuration |
| **Bot WebApp Button URL** | `https://akuma7277.github.io/amorix-bot/webapp/index.html?v=...` | [config.py](file:///c:/Users/HP/OneDrive/Documents/GitHub/amorix-bot/config.py#L70), [reply.py](file:///c:/Users/HP/OneDrive/Documents/GitHub/amorix-bot/reply.py#L10) (`get_webapp_url()`) |
| **API Base URL** | `https://amorix-bot-production.up.railway.app` | Railway Public Domain / [webapp/app.js](file:///c:/Users/HP/OneDrive/Documents/GitHub/amorix-bot/webapp/app.js) |
| **Frontend Hosting** | GitHub Pages HTTPS (`https://akuma7277.github.io/amorix-bot/webapp/index.html`) & Railway Static (`https://amorix-bot-production.up.railway.app/`) | `curl -I` status `200 OK` |
| **Build Marker** | `Kairyx build: v2.29.0` | Visible in `#verifyingScreen` and `#buildVersionBadge` |

---

## 2. Live Endpoint Tests Matrix

```text
[HEALTH_ENDPOINT]: HTTP 200 OK -> {"status": "ok"}
[HEALTH_READY]:    HTTP 200 OK -> {"status": "ready", "database": "connected"}
[SESSION_UNAUTH]:  HTTP 401 Unauthorized -> {"success": false, "error": {"code": "AUTH_FAILED"}}
[SESSION_VALID]:   HTTP 200 OK -> {"success": true, "user_status": "DRAFT", "user": {"id": 10, ...}}
[CORS_PREFLIGHT]:  HTTP 200 OK -> Access-Control-Allow-Origin: *
[FRONTEND_SPA]:    HTTP 200 OK -> Verified v2.29.0 assets
```

---

## 3. Session Normalization & Routing Verification

- **Function**: `normalizeSession(rawPayload)`
- **Behavior**:
  - Extracts `normalizedStatus` from `user_status` / `user.status`.
  - For `DRAFT`: Transitions state to `READY` $\rightarrow$ calls `showView('registrationScreen')` $\rightarrow$ immediately displays Step 1 (Language Selection) and Step 2 (Date of Birth Picker).
  - For `PENDING_APPROVAL`: Transitions state to `READY` $\rightarrow$ calls `showView('pendingScreen')`.
  - For `APPROVED` / `ACTIVE`: Transitions state to `READY` $\rightarrow$ calls `showView('approvedScreen')` $\rightarrow$ initializes Discover deck and user stats.
  - For `REJECTED` / `BANNED`: Displays dedicated rejection/ban views.
  - For `ERROR` / `TIMEOUT`: AbortController triggers after 15s $\rightarrow$ displays retry button with `REQ-XXXXXX`.
