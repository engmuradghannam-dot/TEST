"""Nexus custom middleware stack: Auth (JWT), Error Handler,
Request Logger, and Validation."""
import json
import logging
import time
import uuid

from django.http import JsonResponse

logger = logging.getLogger("nexus.request")


class RequestLoggerMiddleware:
    """Assigns a request_id, logs method/path/status/duration/user."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = uuid.uuid4().hex[:12]
        t0 = time.monotonic()
        response = self.get_response(request)
        duration_ms = int((time.monotonic() - t0) * 1000)
        user = getattr(request, "user", None)
        logger.info(
            "rid=%s %s %s -> %s %sms user=%s",
            request.request_id, request.method, request.path,
            response.status_code, duration_ms,
            getattr(user, "pk", "-") if user and user.is_authenticated else "-",
        )
        response["X-Request-ID"] = request.request_id
        try:
            if response.status_code >= 500:
                from apps.core.observability import metrics_collector
                metrics_collector.counter("http.5xx.count", 1, {"path": request.path})
        except Exception:
            pass
        return response


class ErrorHandlerMiddleware:
    """Converts unhandled exceptions into a consistent JSON envelope
    (API paths only) and logs the traceback with the request id."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        rid = getattr(request, "request_id", "-")
        logger.exception("rid=%s unhandled error on %s", rid, request.path)
        if request.path.startswith("/api/"):
            return JsonResponse(
                {"error": "internal_error",
                 "message": "An unexpected error occurred.",
                 "request_id": rid},
                status=500,
            )
        return None


class APIAuthMiddleware:
    """Enforces authentication on /api/ paths (DRF handles the actual
    token validation; this blocks anonymous access early and uniformly),
    with a configurable public allowlist."""

    PUBLIC_PREFIXES = ("/api/auth/", "/api/token/", "/api/health/",
                       "/api/docs/", "/api/schema/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith("/api/") and not path.startswith(self.PUBLIC_PREFIXES):
            has_auth = bool(request.META.get("HTTP_AUTHORIZATION")) or (
                getattr(request, "user", None) and request.user.is_authenticated
            )
            if not has_auth:
                return JsonResponse(
                    {"error": "unauthorized",
                     "message": "Authentication credentials were not provided."},
                    status=401,
                )
        return self.get_response(request)


class ValidationMiddleware:
    """Request hygiene: rejects malformed JSON bodies and oversized
    payloads before they reach the views."""

    MAX_BODY_BYTES = 10 * 1024 * 1024  # 10 MB

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            length = int(request.META.get("CONTENT_LENGTH") or 0)
            if length > self.MAX_BODY_BYTES:
                return JsonResponse(
                    {"error": "payload_too_large",
                     "message": f"Body exceeds {self.MAX_BODY_BYTES} bytes."},
                    status=413,
                )
            ctype = request.META.get("CONTENT_TYPE", "")
            if "application/json" in ctype and request.body:
                try:
                    json.loads(request.body)
                except (ValueError, UnicodeDecodeError):
                    return JsonResponse(
                        {"error": "invalid_json",
                         "message": "Request body is not valid JSON."},
                        status=400,
                    )
        return self.get_response(request)
