"""
Simple failed-login lockout tracking, backed by Django's cache framework
(configure a real cache backend such as Redis in production; falls back to
the local-memory cache in development).
"""
import time

from django.conf import settings
from django.core.cache import cache


def _key(identifier: str) -> str:
    return f"login_attempts:{identifier.lower()}"


def register_failed_attempt(identifier: str) -> int:
    key = _key(identifier)
    attempts = cache.get(key, 0) + 1
    cache.set(key, attempts, timeout=settings.LOGIN_LOCKOUT_MINUTES * 60)
    return attempts


def clear_attempts(identifier: str) -> None:
    cache.delete(_key(identifier))


def is_locked_out(identifier: str) -> bool:
    return cache.get(_key(identifier), 0) >= settings.LOGIN_MAX_ATTEMPTS


def seconds_until_unlock(identifier: str) -> int:
    ttl = cache.ttl(_key(identifier)) if hasattr(cache, "ttl") else None
    return ttl or settings.LOGIN_LOCKOUT_MINUTES * 60
