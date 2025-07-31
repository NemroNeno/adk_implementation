import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.crud import crud_stats

from fastapi import APIRouter, Depends
from fastapi.responses import Response 
from app.db.base import get_db
from app.db.models import AuditLog
from app.api.permissions import allow_admin_only

router = APIRouter()

@router.get("/reports/audit-log", dependencies=[Depends(allow_admin_only)])
def export_audit_log(db: Session = Depends(get_db)):
    """
    Exports the complete audit log as a CSV file. Admin only.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["ID", "Timestamp", "UserID", "AgentID", "Action", "Details"])

    # Write data
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    for log in logs:
        writer.writerow([
            log.id,
            log.timestamp.isoformat(),
            log.user_id,
            log.agent_id,
            log.action,
            str(log.details) # Convert JSON to string for CSV
        ])
    
    # Get the CSV string content
    csv_content = output.getvalue()
    output.close()
    
    # --- THE FIX IS HERE ---
    # Return a standard Response with the correct media type and headers
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=audit_log_export.csv"
        }
    )


@router.get("/analytics", dependencies=[Depends(allow_admin_only)])
def get_system_analytics(db: Session = Depends(get_db)):
    """
    Retrieves system-wide analytics. Admin only.
    """
    # Just one simple function call!
    analytics = crud_stats.get_platform_analytics(db)
    return analytics