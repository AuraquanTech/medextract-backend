import uvicorn
from fastapi import FastAPI, Request
from src.infra.config import get_settings
from src.infra.logging import configure_logging, request_id
from src.api.routers import health, analyze, experts, similar, whatif, audit, stripe_webhooks

def build_app() -> FastAPI:
    cfg = get_settings()
    configure_logging(cfg.log_level)
    app = FastAPI(title="MedExtractAI", version="2.0.0")
    app.include_router(health.router)
    app.include_router(analyze.router)
    app.include_router(experts.router)
    app.include_router(similar.router)
    app.include_router(whatif.router)
    app.include_router(audit.router)
    app.include_router(stripe_webhooks.router)

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        rid = request.headers.get("X-Request-ID") or "req-unknown"
        token = request_id.set(rid)
        try:
            resp = await call_next(request)
        finally:
            request_id.reset(token)
        return resp

    return app

app = build_app()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000)
