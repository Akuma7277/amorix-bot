# KAIRYX MINI APP — SESSION FAILURE EVIDENCE & DIAGNOSTIC AUDIT (`SESSION_FAILURE_EVIDENCE.md`)

---

## 1. Failure Reproduction & Forensic Audit

### A. First Red Console Errors Identified (Pre-Fix)
1. **DOM Listener Null-Pointer on Script Load**:
   - Error: `Uncaught TypeError: Cannot read properties of null (reading 'addEventListener')`
   - File & Line: `webapp/app.js` (former Line 829)
   - Root Cause: Script attempted to attach listener to `document.getElementById('regPhotoInput')`, which had been renamed to `kairyxPhotoInput` in HTML. Because this ran synchronously at the top level of `app.js`, it halted script parsing before `verifySession()` could execute.
2. **Missing Wizard Steps in HTML DOM**:
   - Error: `Uncaught TypeError: Cannot read properties of null (reading 'style')` when navigating wizard
   - File & Line: `webapp/app.js` in `nextRegStep()`
   - Root Cause: `regStep3` and `regStep6` container DIVs were missing from `webapp/index.html`.
3. **Duplicate Event Listener at Startup**:
   - Duplicate `editPhotoFileInput` listener on Lines 1434 and 2147.

---

## 2. API Session Request Verification

| Parameter | Value |
|---|---|
| **Request URL** | `https://amorix-bot-production.up.railway.app/api/session` |
| **HTTP Method** | `GET` |
| **Headers** | `Accept: application/json`, `X-TG-Init-Data: <raw initData>`, `X-Request-ID: REQ-XXXXXX` |
| **HTTP Status** | `200 OK` (with valid TG initData) / `401 Unauthorized` (without initData) |
| **Response Duration** | `~120ms` (Direct HTTP) |
| **CORS Status** | Preflight `OPTIONS 200 OK`, `Access-Control-Allow-Origin: *` |
| **Response Shape** | `{"success": true, "user_status": "DRAFT", "user": {"id": 10, ...}}` |

---

## 3. Session State Machine & Routing Verification

```
[BOOT] Window Load / Script Start
   ↓
[STATE: IDLE -> LOADING]
   ↓
[INIT_DATA_CHECK]
   ├─ If initData is missing (outside Telegram):
   │     [STATE: ERROR]
   │     Render: "Telegram sessiyasi topilmadi. Mini App’ni Telegram bot (@Ka1ryx_bot) ichidan qayta oching."
   │     Buttons: [🤖 Botni ochish] [⚡ Demo rejim]
   │
   └─ If initData is present:
         15-second AbortController timeout started
         Fetch GET https://amorix-bot-production.up.railway.app/api/session
         Headers: X-TG-Init-Data, X-Request-ID
         ↓
         normalizeSessionResponse(payload)
         ↓
         [STATE: READY]
         Status Routing:
           • DRAFT            → showView('registrationScreen') (Step 1..7)
           • PENDING_APPROVAL → showView('pendingScreen')
           • REJECTED         → showView('rejectedScreen')
           • BANNED           → showView('bannedScreen')
           • APPROVED/ACTIVE  → showView('approvedScreen')
```

---

## 4. Verification Evidence Matrix

| Flow | Status | Evidence / Result |
|---|---|---|
| **Health Probe** | `PASS` | `GET /health` $\rightarrow$ `HTTP 200 OK` |
| **Database Ready** | `PASS` | `GET /health/ready` $\rightarrow$ `HTTP 200 OK` (`{"status": "ready", "database": "connected"}`) |
| **Unauthorized Session** | `PASS` | `GET /api/session` $\rightarrow$ `HTTP 401 Unauthorized` |
| **Valid TG HMAC Auth** | `PASS` | `GET /api/session` $\rightarrow$ `HTTP 200 OK` (`user_status: DRAFT`) |
| **Draft User Routing** | `PASS` | Leaves loading screen $\rightarrow$ Renders `registrationScreen` Step 1 |
| **Wizard Navigation** | `PASS` | Steps 1 through 7 navigate smoothly with zero DOM exceptions |
| **Build & Cache** | `PASS` | Version `v2.28.0` with strict no-cache meta tags |
