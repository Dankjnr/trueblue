"""
Firebase Cloud Messaging integration. Isolated from services.py so the
firebase-admin dependency is only imported when push is actually
configured (FIREBASE_CREDENTIALS_JSON set).
"""
import json
import logging

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, messaging

logger = logging.getLogger("trueblue.notifications")

_app = None


def _get_app():
    global _app
    if _app is None:
        cred = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS_JSON))
        _app = firebase_admin.initialize_app(cred)
    return _app


def send_fcm_message(tokens: list[str], title: str, body: str, data: dict) -> bool:
    _get_app()
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in data.items()},
        tokens=tokens,
    )
    try:
        response = messaging.send_multicast(message)
        return response.success_count > 0
    except Exception:
        logger.exception("FCM send failed")
        return False
