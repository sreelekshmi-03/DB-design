"""
Centralized DRF exception handling - Day 13 deliverable.

Wires into DRF via settings.REST_FRAMEWORK["EXCEPTION_HANDLER"]. Every error
that DRF would normally turn into a response (validation errors, auth
errors, permission errors, not-found, method-not-allowed, throttling, etc.)
gets routed through here first, so every error response the API returns has
the SAME shape - instead of each exception type producing a differently
shaped body (which is what you get with DRF's defaults: sometimes
{"detail": "..."}, sometimes {"field": ["msg"]}, sometimes a bare list).

Standard error response shape (every non-2xx response):
{
    "success": false,
    "status_code": 400,
    "message": "Human-readable one-line summary",
    "errors": {...} | null
}

This file does NOT touch success responses - those still come back however
each view already builds them (see response.py for an optional helper if
you want success responses standardized too).
"""
import logging

from rest_framework.views import exception_handler as drf_default_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Drop-in replacement for DRF's default exception_handler.
    settings.py wires this in with:
        REST_FRAMEWORK = {..., "EXCEPTION_HANDLER": "app.exceptions.custom_exception_handler"}
    """
    response = drf_default_handler(exc, context)

    if response is None:
        # drf_default_handler only handles APIException / Http404 /
        # PermissionDenied. Anything else (a bare bug - e.g. a NoneType
        # error, an IntegrityError, an AttributeError in a view/signal)
        # falls through to here as an unhandled 500.
        #
        # IMPORTANT: we log the full traceback here ourselves, because
        # returning a Response (instead of None / re-raising) stops DRF
        # from ever re-raising this exception up to Django - so without
        # this log line, the real crash reason would never appear
        # anywhere, not even in the runserver console.
        logger.error(
            "Unhandled exception in %s", context.get("view"), exc_info=exc
        )
        return Response(
            {
                "success": False,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "Internal server error. Please try again, and report this if it keeps happening.",
                "errors": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    message, errors = _extract_message_and_errors(response.data)

    response.data = {
        "success": False,
        "status_code": response.status_code,
        "message": message,
        "errors": errors,
    }
    return response


def _extract_message_and_errors(data):
    """
    DRF's response.data shape varies by exception type - normalize all of
    them into a single (message, errors) pair:

      - {"detail": "..."}                     -> NotFound, PermissionDenied,
                                                   NotAuthenticated, AuthenticationFailed,
                                                   MethodNotAllowed, Throttled
      - {"field": ["err1"], "other": ["err2"]} -> serializer ValidationError
      - ["non field error"]                    -> list-only validation errors
    """
    if isinstance(data, dict) and "detail" in data:
        message= str(data["detail"])
        extra={k: v for k,v in data.items() if k!="detail"}
        return message,(extra or None)

    if isinstance(data, dict) and data:
        first_field = next(iter(data))
        first_error = data[first_field]
        if isinstance(first_error, list) and first_error:
            message = f"{first_field}: {first_error[0]}"
        else:
            message = "Validation failed."
        return message, data

    if isinstance(data, list) and data:
        return str(data[0]), {"non_field_errors": data}

    return "An error occurred.", data