"""In-app notification storage with read/unread tracking."""
import logging
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# In-memory store (use DB in production)
_notifications: dict[str, dict] = {}


def create_notification(
    user_id: str,
    watch_rule_id: str | None,
    document_id: str | None,
    channel: str,
    subject: str,
    body: str,
) -> dict:
    """Store an in-app notification."""
    notif_id = str(uuid.uuid4())
    notification = {
        "id": notif_id,
        "user_id": user_id,
        "watch_rule_id": watch_rule_id,
        "document_id": document_id,
        "channel": channel,
        "subject": subject,
        "body": body,
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _notifications[notif_id] = notification
    return notification


def get_user_notifications(user_id: str, page: int = 1, page_size: int = 20) -> dict:
    """Get paginated notifications for a user."""
    user_notifs = [n for n in _notifications.values() if n["user_id"] == user_id]
    user_notifs.sort(key=lambda n: n["created_at"], reverse=True)

    start = (page - 1) * page_size
    end = start + page_size
    paged = user_notifs[start:end]

    return {
        "notifications": paged,
        "total": len(user_notifs),
        "unread": sum(1 for n in user_notifs if not n["is_read"]),
        "page": page,
        "page_size": page_size,
    }


def mark_as_read(notification_id: str, user_id: str) -> bool:
    """Mark a notification as read. Returns False if not found or wrong user."""
    notif = _notifications.get(notification_id)
    if not notif or notif["user_id"] != user_id:
        return False
    notif["is_read"] = True
    return True


def batch_mark_as_read(notification_ids: list[str], user_id: str) -> int:
    """Mark multiple notifications as read. Returns count of updated."""
    count = 0
    for nid in notification_ids:
        if mark_as_read(nid, user_id):
            count += 1
    return count
