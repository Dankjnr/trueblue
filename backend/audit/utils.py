from .middleware import get_current_ip
from .models import AuditLog


def log_action(actor, action: str, target=None, metadata: dict | None = None):
    """
    Write an audit entry. `target` may be any model instance (its class
    name and pk are recorded) or None for account-level actions.
    """
    target_type = target.__class__.__name__ if target is not None else ""
    target_id = str(getattr(target, "pk", "")) if target is not None else ""
    AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", True) else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata or {},
        ip_address=get_current_ip(),
    )
