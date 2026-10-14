"""Flask API that serves recommendations."""
import logging
import os
import time
import uuid
from threading import Lock

from flask import Flask, g, jsonify, request

from data.database import get_session, init_db
from engine.orchestrator import (ContentNotFoundError,
                                 RecommendationOrchestrator,
                                 UserNotFoundError)

logger = logging.getLogger("recommender.api")


def is_whole_number(value):
    """True for whole numbers (but not True/False)."""
    return isinstance(value, int) and not isinstance(value, bool)


def create_app(orchestrator=None, api_key=None):
    """Build and return the Flask app.

    Tests can pass in their own orchestrator; otherwise the real database
    is used. If api_key is given, every endpoint except /health needs it
    in an X-API-Key header.
    """
    app = Flask(__name__)

    if orchestrator is None:
        init_db()
        orchestrator = RecommendationOrchestrator(get_session())

    # The database session is not thread-safe, so one request at a time
    # may use the engine.
    engine_lock = Lock()

    # Numbers for the /metrics endpoint
    stats = {"requests": 0, "errors": 0, "total_ms": 0.0}
    stats_lock = Lock()
    started_at = time.time()

    def error(status, message):
        """Build a JSON error response."""
        body = {"error": message, "request_id": g.request_id}
        return jsonify(body), status

    @app.before_request
    def start_request():
        """Start a timer and give every request an id for tracing."""
        g.start = time.time()
        g.request_id = (request.headers.get("X-Request-ID")
                        or uuid.uuid4().hex[:8])
        if api_key and request.path != "/health":
            if request.headers.get("X-API-Key") != api_key:
                return error(401, "missing or invalid API key")

    @app.after_request
    def finish_request(response):
        """Log the request and add its id to the response headers."""
        elapsed_ms = (time.time() - g.start) * 1000
        response.headers["X-Request-ID"] = g.request_id
        with stats_lock:
            stats["requests"] += 1
            stats["total_ms"] += elapsed_ms
            if response.status_code >= 400:
                stats["errors"] += 1
        logger.info("%s %s %s -> %s (%.1f ms)", g.request_id,
                    request.method, request.path, response.status_code,
                    elapsed_ms)
        return response

    @app.errorhandler(404)
    def not_found(exc):
        return error(404, "route not found")

    @app.errorhandler(405)
    def wrong_method(exc):
        return error(405, "method not allowed")

    @app.errorhandler(Exception)
    def unexpected(exc):
        logger.exception("unexpected error")
        return error(500, "internal server error")

    @app.route("/health")
    def health():
        """Simple check that the service is running."""
        return jsonify({"status": "ok"})

    @app.route("/recommend/<user_id>")
    def recommend(user_id):
        """Return recommendations for a user: /recommend/5?limit=3"""
        if not user_id.isdigit():
            return error(400, "user_id must be a whole number")
        limit = request.args.get("limit", "5")
        if not limit.isdigit() or not 1 <= int(limit) <= 50:
            return error(400, "limit must be a whole number from 1 to 50")

        try:
            with engine_lock:
                results = orchestrator.get_recommendations(int(user_id),
                                                           int(limit))
        except UserNotFoundError as exc:
            return error(404, str(exc))

        return jsonify({
            "user_id": int(user_id),
            "count": len(results),
            "recommendations": results,
            "request_id": g.request_id,
        })

    @app.route("/feedback", methods=["POST"])
    def feedback():
        """Record feedback. JSON body: user_id, content_id, type, rating."""
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return error(400, "request body must be a JSON object")
        for field in ("user_id", "content_id"):
            if not is_whole_number(data.get(field)):
                return error(400, field + " must be a whole number")
        kind = data.get("type")
        if not isinstance(kind, str):
            return error(400, "type is required")
        rating = data.get("rating")
        if rating is not None and not is_whole_number(rating):
            return error(400, "rating must be a whole number from 1 to 5")

        try:
            with engine_lock:
                orchestrator.record_feedback(data["user_id"],
                                             data["content_id"], kind, rating)
        except (UserNotFoundError, ContentNotFoundError) as exc:
            return error(404, str(exc))
        except ValueError as exc:
            return error(400, str(exc))

        return jsonify({"status": "recorded",
                        "request_id": g.request_id}), 201

    @app.route("/metrics")
    def metrics():
        """Basic performance numbers."""
        with stats_lock:
            count = stats["requests"]
            errors = stats["errors"]
            average = stats["total_ms"] / count if count else 0.0
        with engine_lock:
            cache = orchestrator.cache_stats()
        return jsonify({
            "requests": count,
            "errors": errors,
            "average_response_ms": round(average, 2),
            "uptime_seconds": round(time.time() - started_at, 1),
            "cache": cache,
        })

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    create_app(api_key=os.environ.get("API_KEY")).run(port=5000)
