import threading

_local = threading.local()


def get_current_ip():
    return getattr(_local, "ip", None)


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class RequestContextMiddleware:
    """Stashes the requesting client's IP so log_action() can read it
    without every call site having to thread the request through."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.ip = _client_ip(request)
        try:
            response = self.get_response(request)
        finally:
            _local.ip = None
        return response
