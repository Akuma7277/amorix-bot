"""
Kairyx MVP REST API - Phase 0
Minimal Hello World API server for connection verification.
"""
import os
import json
import logging
from datetime import datetime
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_health(request):
    return web.json_response({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    })

async def handle_test(request):
    return web.json_response({
        "message": "api works",
        "timestamp": datetime.now().isoformat()
    })

async def handle_index(request):
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(webapp_dir, "index.html")
    if os.path.exists(index_path):
        response = web.FileResponse(index_path)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return web.json_response({"message": "Kairyx API Server - Phase 0"})

async def serve_style(request):
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    style_path = os.path.join(webapp_dir, "style.css")
    if os.path.exists(style_path):
        return web.FileResponse(style_path)
    return web.Response(text="/* style.css not found */", content_type="text/css")

async def serve_app(request):
    import os
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(webapp_dir, "app.js")
    if os.path.exists(app_path):
        return web.FileResponse(app_path)
    return web.Response(text="// app.js not found", content_type="application/javascript")

def create_webapp_app() -> web.Application:
    app = web.Application()

    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            if request.method == "OPTIONS":
                response = web.Response(status=200)
            else:
                response = await handler(request)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-TG-Init-Data"
            return response
        return middleware_handler

    app.middlewares.append(cors_middleware)

    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/api/test", handle_test)
    app.router.add_get("/style.css", serve_style)
    app.router.add_get("/app.js", serve_app)

    return app

if __name__ == "__main__":
    app = create_webapp_app()
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
