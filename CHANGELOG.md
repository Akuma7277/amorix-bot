# CHANGELOG — Kairyx Enterprise Mini App

---

## [2.28.0] - 2026-08-22

### 🚀 Critical Fixes & Improvements
- **Session State Machine Standardization**:
  - Implemented formal `IDLE -> LOADING -> READY / ERROR` lifecycle.
  - Added strict 15-second `AbortController` timeout for all auth and session handshakes.
  - Added single-flight request guard to prevent duplicate concurrent network calls.
  - Added standardized `normalizeSessionResponse()` helper to unify `user_status` and `user.status`.
  - Added `X-Request-ID` tracking headers (`REQ-XXXXXX`) across all frontend API invocations.
  - Added dedicated out-of-Telegram guidance: *"Telegram sessiyasi topilmadi. Mini App’ni Telegram bot (@Ka1ryx_bot) ichidan qayta oching."*
- **DOM & Wizard Robustness**:
  - Standardized photo uploader input ID to `kairyxPhotoInput` across `webapp/index.html` and `webapp/app.js`.
  - Removed duplicate `editPhotoFileInput` event listeners.
  - Restored full 7-step wizard DOM containers (`regStep1` .. `regStep7`) with zero null-pointer exceptions.
- **Cache Busting & Network Resilience**:
  - Bumped frontend build asset version to `v2.28.0`.
  - Configured strict no-cache HTTP headers on index HTML responses.
  - Added safe `web.HTTPException` handling in backend middleware to prevent false 500 error logs.
