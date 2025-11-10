"""Health check endpoints for SLO monitoring.

Provides liveness, readiness, and composite health checks:
- /livez: Process is alive (quick check)
- /readyz: Dependencies ready (DB, cache, external APIs)
- /healthz: Composite check used by load balancers and CI
"""

import logging
from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

bp = Blueprint("health", __name__, url_prefix="")


@bp.get("/livez")
def livez():
    """Liveness probe: Process is alive.
    
    Returns:
        (dict, int): {"ok": true} with 200 if process is responsive
        (dict, int): {"ok": false, "error": str} with 503 if not
    """
    try:
        # Minimal check - just verify Flask app is responsive
        return jsonify(ok=True, status="alive"), 200
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return jsonify(ok=False, error=str(e)), 503


@bp.get("/readyz")
def readyz():
    """Readiness probe: Dependencies are ready.
    
    Checks:
    - Database connectivity
    - Cache availability (if configured)
    - External APIs (Stripe, etc.)
    
    Returns:
        (dict, int): {"ok": true, "deps": {...}} with 200 if ready
        (dict, int): {"ok": false, "failed": [...]} with 503 if not
    """
    deps = {}
    failed = []
    
    # Check database
    try:
        from app.src.infra.database import db
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        deps["database"] = "ok"
    except SQLAlchemyError as e:
        logger.warning(f"Database readiness check failed: {e}")
        deps["database"] = "failed"
        failed.append("database")
    except Exception as e:
        logger.warning(f"Database check error: {e}")
        deps["database"] = "error"
        failed.append("database")
    
    # Check Stripe API availability (lightweight)
    try:
        import stripe
        import os
        
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if stripe.api_key:
            # List recent charges with minimal data (no side effects)
            stripe.Charge.list(limit=1)
            deps["stripe"] = "ok"
    except stripe.error.StripeConnectionError as e:
        logger.warning(f"Stripe connectivity check failed: {e}")
        deps["stripe"] = "unreachable"
        failed.append("stripe")
    except Exception as e:
        logger.debug(f"Stripe check (optional): {e}")
        deps["stripe"] = "skipped"
    
    # If critical dependencies failed, return 503
    if failed:
        return jsonify(
            ok=False,
            status="not_ready",
            failed=failed,
            deps=deps
        ), 503
    
    return jsonify(
        ok=True,
        status="ready",
        deps=deps
    ), 200


@bp.get("/healthz")
def healthz():
    """Composite health check for load balancers and CI.
    
    Combines liveness and readiness:
    - 200: Fully healthy (live + ready)
    - 206: Partially healthy (live + some deps down)
    - 503: Unhealthy (not live or critical dep down)
    
    Returns:
        (dict, int): Comprehensive health state
    """
    try:
        # Check liveness first
        live_resp, live_code = livez()
        if live_code != 200:
            return jsonify(
                ok=False,
                status="not_alive",
                liveness=live_code
            ), 503
        
        # Check readiness
        from flask import current_app
        with current_app.app_context():
            ready_resp, ready_code = readyz()
        
        if ready_code == 200:
            # Fully healthy
            return jsonify(
                ok=True,
                status="healthy",
                checks={
                    "liveness": 200,
                    "readiness": 200
                }
            ), 200
        else:
            # Degraded but alive
            import json
            ready_data = json.loads(ready_resp.get_data(as_text=True))
            return jsonify(
                ok=False,
                status="degraded",
                checks={
                    "liveness": 200,
                    "readiness": ready_code
                },
                failed_deps=ready_data.get("failed", [])
            ), 206
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify(
            ok=False,
            status="error",
            error=str(e)
        ), 503


def register_health_endpoints(app):
    """Register health check blueprint with Flask app.
    
    Usage:
        from app.src.services.health import register_health_endpoints
        register_health_endpoints(app)
    """
    app.register_blueprint(bp)
    logger.info("Health check endpoints registered: /livez, /readyz, /healthz")
