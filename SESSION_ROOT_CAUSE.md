# KAIRYX TELEGRAM MINI APP — SESSION & AUTH DIAGNOSTIC REPORT (`SESSION_ROOT_CAUSE.md`)

---

## 1. Executive Summary & Architecture Trace

| Item | Details |
|---|---|
| **Frontend Auth Entry** | [webapp/app.js](file:///c:/Users/HP/OneDrive/Documents/GitHub/amorix-bot/webapp/app.js) in function `verifySession()` |
| **API Endpoint** | `GET /api/session?initData=...` |
| **Production API URL** | `https://amorix-bot-production.up.railway.app` |
| **Frontend Hosting** | GitHub Pages (`https://akuma7277.github.io/amorix-bot/webapp/index.html`) & Railway Static (`https://amorix-bot-production.up.railway.app/`) |
| **Railway Service & Command** | `web: python bot.py` (via `Procfile`) |
| **Port Binding** | `os.getenv("PORT", 8080)` bound strictly to `0.0.0.0` via `aiohttp.web.TCPSite` |
| **Telegram SDK** | `<script src="https://telegram.org/js/telegram-web-app.js"></script>` loaded synchronously in `<head>` |
| **InitData Transport** | Headers `X-TG-Init-Data`, `Authorization: Bearer <initData>`, and URL Query `?initData=...` |
| **HMAC Validation** | Server verifies SHA256 HMAC of sorted key-value pairs with secret key `HMAC_SHA256(b"WebAppData", BOT_TOKEN)` |
| **CORS Policy** | `Access-Control-Allow-Origin: *`, `Access-Control-Allow-Headers: Content-Type, Authorization, X-TG-Init-Data`, `Access-Control-Allow-Methods: GET, POST, OPTIONS` |

---

## 2. Real Root Causes of Previous Loading Screen Hangs

1. **DOM Access Null Pointer Exception (Line 829)**:
   - `regPhotoInput` was renamed to `kairyxPhotoInput` in HTML without updating a synchronous event listener in `app.js`.
   - Result: Synchronous script crashed before `verifySession()` could execute.
2. **Missing Wizard Steps in HTML DOM**:
   - `regStep3` and `regStep6` were missing from the wizard DOM, causing registration step transitions to throw uncaught exceptions.
3. **Aggressive Mobile In-App WebView Caching**:
   - Telegram for iOS/Android aggressively cached the old `app.js` bundle without no-cache headers.
4. **Unhandled HTTPException in Middleware**:
   - Generic exception logging treated standard 404s/favicon requests as 500 errors.

---

## 3. Standardized Session State Machine

```
               +--------------------------------------------------+
               |                      IDLE                        |
               +--------------------------------------------------+
                                        |
                                        v
               +--------------------------------------------------+
               |                    LOADING                       |
               | (15s AbortController, Request ID, Safe Logging)   |
               +--------------------------------------------------+
                        /                       \
                       /                         \
                      v                           v
   +------------------------------------+  +-------------------------------------+
   |               READY                |  |                ERROR                |
   | • DRAFT -> /register (Step 1..7)   |  | • 401 / Invalid -> Session Error   |
   | • PENDING_APPROVAL -> /pending     |  | • Missing TG InitData -> Bot Prompt|
   | • REJECTED -> /rejected            |  | • 500 / Network -> Retry Screen     |
   | • BANNED -> /banned                |  | • Request ID Displayed              |
   | • APPROVED/ACTIVE -> /home         |  +-------------------------------------+
   +------------------------------------+
```

---

## 4. Response Shape Standard

### Success Response (`HTTP 200 OK`):
```json
{
  "success": true,
  "is_admin": false,
  "user_status": "DRAFT",
  "user": {
    "id": 9,
    "telegram_id": 9988776655,
    "username": "user_name",
    "role": "USER",
    "status": "DRAFT",
    "name": null,
    "age": null,
    "gender": "OTHER",
    "target_gender": "ANY",
    "city": null,
    "photo": null,
    "bio": null,
    "interests": [],
    "language": "uz",
    "balance": 0.0,
    "bonus_points": 0,
    "plan_tier": "FREE",
    "is_premium": false,
    "xp": 50,
    "level": 1,
    "streak_days": 0,
    "badges": [],
    "referral_count": 0,
    "is_verified": false
  },
  "unread_notifications": 1,
  "likes_received_count": 0
}
```

### Error Response (`HTTP 401 / 500`):
```json
{
  "success": false,
  "error": {
    "code": "AUTH_FAILED",
    "message": "Session could not be verified",
    "request_id": "a1b2c3d4"
  }
}
```
