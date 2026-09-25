"""
Thin provider-agnostic wrappers around SMS and push notifications, so the
rest of the codebase never talks to Termii/Firebase directly. Swap the
implementation here if the provider changes.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger("trueblue.notifications")


def send_sms(phone_number: str, message: str) -> bool:
    """Send an SMS via the configured provider. Returns True on success."""
    if settings.SMS_PROVIDER == "termii":
        return _send_via_termii(phone_number, message)
    logger.warning("Unknown SMS_PROVIDER=%s; message not sent.", settings.SMS_PROVIDER)
    return False


def _send_via_termii(phone_number: str, message: str) -> bool:
    if not settings.SMS_API_KEY:
        logger.info("[dev] SMS to %s: %s", phone_number, message)
        return True
    try:
        response = requests.post(
            "https://api.ng.termii.com/api/sms/send",
            json={
                "to": phone_number,
                "from": settings.SMS_SENDER_ID,
                "sms": message,
                "type": "plain",
                "channel": "generic",
                "api_key": settings.SMS_API_KEY,
            },
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        logger.exception("Failed to send SMS to %s", phone_number)
        return False


def send_push(user, title: str, body: str, data: dict | None = None) -> bool:
    """Send a push notification via Firebase Cloud Messaging to a user's
    registered device tokens. No-op (logged) if push isn't configured."""
    if not settings.FIREBASE_CREDENTIALS_JSON:
        logger.info("[dev] Push to %s: %s — %s", user, title, body)
        return True

    from .push import send_fcm_message  # imported lazily; needs firebase-admin

    tokens = list(user.device_tokens.values_list("token", flat=True))
    if not tokens:
        return False
    return send_fcm_message(tokens, title, body, data or {})


def notify_job_offer(cleaner, job):
    send_sms(
        cleaner.user.phone_number,
        f"New TrueBlue job: {job.location_summary}, {job.cleaners_needed} cleaner(s) needed on "
        f"{job.requested_date}. Reply CONFIRM or open the app to accept.",
    )
    send_push(
        cleaner.user,
        "New job offer",
        f"{job.location_summary} on {job.requested_date}",
        data={"job_id": str(job.id), "type": "job_offer"},
    )


def notify_job_packet(cleaner, job):
    send_sms(
        cleaner.user.phone_number,
        f"Job confirmed for {job.requested_date}. Check the app for the access code and instructions.",
    )
    send_push(
        cleaner.user,
        "Job details ready",
        "Start time, access code, and instructions have been sent.",
        data={"job_id": str(job.id), "type": "job_packet"},
    )


def notify_admin_response(admins_queryset, job, outcome: str):
    for admin_user in admins_queryset:
        send_push(
            admin_user,
            "Job update",
            f"{job.location_summary}: cleaner {outcome}.",
            data={"job_id": str(job.id), "type": "job_response"},
        )
