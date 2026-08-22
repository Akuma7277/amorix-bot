# ROOT CAUSE ANALYSIS — Kairyx Telegram Mini App

---

## 1. Primary Root Causes of Loading Screen Freezes

1. **Synchronous JavaScript Exception on DOM Query**:
   - `webapp/app.js` contained a synchronous listener targeting `regPhotoInput` (renamed to `kairyxPhotoInput` in HTML).
   - This threw an unhandled `TypeError` before `verifySession()` could register or execute.
2. **Missing Wizard Containers**:
   - `regStep3` and `regStep6` were missing from `webapp/index.html`, causing step transitions to fail.
3. **Ambiguous `WEBAPP_URL` Resolution in Bot Configuration**:
   - On Railway, `config.py` prioritized `RAILWAY_PUBLIC_DOMAIN` (`https://amorix-bot-production.up.railway.app`) over the canonical GitHub Pages frontend.
   - Fixed by explicitly defining `CANONICAL_FRONTEND_URL = "https://akuma7277.github.io/amorix-bot/webapp/index.html"`.
4. **Session Response Status Normalization**:
   - Response payload contained `user_status` and `user.status`.
   - Unified via `normalizeSession()` to guarantee exact routing to `registrationScreen` for `DRAFT` users.
