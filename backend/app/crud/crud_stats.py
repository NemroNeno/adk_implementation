from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timedelta

from app.db import models

def get_platform_analytics(db: Session):
    """
    Gathers various analytics from across the platform.
    """
    total_users = db.query(func.count(models.User.id)).scalar()
    total_agents = db.query(func.count(models.Agent.id)).scalar()
    total_messages = db.query(func.count(models.ChatMessage.id)).scalar()
    
    # Calculate average response time for AI messages that have one
    avg_response_time = db.query(func.avg(models.ChatMessage.response_time_seconds))\
        .filter(models.ChatMessage.role == 'ai', models.ChatMessage.response_time_seconds.isnot(None))\
        .scalar()
        
    # Calculate total tokens used
    # Note: This is a simplified sum. For JSONB in PostgreSQL, you might need a more complex query.
    # We will handle the summation in Python for compatibility.
    token_usage_results = db.query(models.ChatMessage.token_usage)\
        .filter(models.ChatMessage.role == 'ai', models.ChatMessage.token_usage.isnot(None))\
        .all()
        
    total_tokens = 0
    if token_usage_results:
        for usage in token_usage_results:
            if usage[0] and 'total_tokens' in usage[0]:
                total_tokens += usage[0]['total_tokens']

    # Get message count over the last 7 days for a time-series chart
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    messages_last_7_days = db.query(
        func.date(models.ChatMessage.timestamp).label('date'),
        func.count(models.ChatMessage.id).label('count')
    ).filter(
        models.ChatMessage.timestamp >= seven_days_ago
    ).group_by(
        func.date(models.ChatMessage.timestamp)
    ).order_by(
        func.date(models.ChatMessage.timestamp)
    ).all()

    # Format the time series data for the frontend chart
    time_series_data = [
        {"date": result.date.strftime("%Y-%m-%d"), "messages": result.count}
        for result in messages_last_7_days
    ]

    return {
        "total_users": total_users,
        "total_agents": total_agents,
        "total_messages": total_messages,
        "avg_response_time": float(avg_response_time) if avg_response_time else 0,
        "total_tokens_used": total_tokens,
        "messages_time_series": time_series_data
    }