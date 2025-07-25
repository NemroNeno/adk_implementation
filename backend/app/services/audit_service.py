from sqlalchemy.orm import Session
from app.db.models import AuditLog
from typing import Optional, Dict, Any

def log_activity(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    Creates an audit log entry.
    """
    log_entry = AuditLog(
        user_id=user_id,
        agent_id=agent_id,
        action=action,
        details=details
    )
    db.add(log_entry)
    db.commit()