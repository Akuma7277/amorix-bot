"""
Amorix Mini App - REST API Server
Telegram Mini App uchun REST API endpointlar.
aiohttp yordamida ishlaydi va bot bilan birga ishga tushadi.
"""
import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qs

from aiohttp import web

logger = logging.getLogger(__name__)


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict | None:
    """
    Telegram WebApp initData ni tekshiradi.
    Muvaffaqiyatli bo'lsa, foydalanuvchi ma'lumotlarini qaytaradi.
    """
    try:
        parsed = parse_qs(init_data)
        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            return None

        # Remove hash from data
        data_check_string = "\n".join(
            f"{k}={v[0]}" for k, v in sorted(parsed.items()) if k != "hash"
        )

        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if computed_hash != received_hash:
            return None

        user_data = parsed.get("user", [None])[0]
        if user_data:
            return json.loads(user_data)
        return None
    except Exception as e:
        logger.warning(f"initData validation failed: {e}")
        return None


async def handle_profile(request):
    """GET /api/profile - Foydalanuvchi profilini qaytaradi."""
    return web.json_response({
        "status": "ok",
        "message": "Profile endpoint - bot orqali ma'lumotlar olinadi",
    })


async def handle_profiles(request):
    """GET /api/profiles - Qidiruv natijalari."""
    return web.json_response({
        "status": "ok",
        "profiles": [],
        "message": "Profillar bot orqali yuklanadi",
    })


async def handle_like(request):
    """POST /api/like - Layk bosish."""
    return web.json_response({
        "status": "ok",
        "message": "Like action - bot orqali amalga oshiriladi",
    })


async def handle_matches(request):
    """GET /api/matches - Matchlar ro'yxati."""
    return web.json_response({
        "status": "ok",
        "matches": [],
    })


async def handle_premium(request):
    """GET /api/premium - Premium holati."""
    return web.json_response({
        "status": "ok",
        "is_premium": False,
        "plan": "basic",
    })


def create_webapp_app() -> web.Application:
    """Mini App uchun aiohttp ilovasini yaratadi."""
    app = web.Application()

    # CORS headers
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            if request.method == "OPTIONS":
                response = web.Response(status=200)
            else:
                response = await handler(request)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response
        return middleware_handler

    app.middlewares.append(cors_middleware)

    # API routes
    app.router.add_get("/api/profile", handle_profile)
    app.router.add_get("/api/profiles", handle_profiles)
    app.router.add_post("/api/like", handle_like)
    app.router.add_get("/api/matches", handle_matches)
    app.router.add_get("/api/premium", handle_premium)

    # Static files (webapp/)
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    app.router.add_static("/", webapp_dir, show_index=True)

    return app


if __name__ == "__main__":
    app = create_webapp_app()
    web.run_app(app, host="0.0.0.0", port=8080)
