# backend/app/crud/crud_stats.py

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timedelta

from app.db import models

def get_platform_analytics(db: Session):
    """
    Gathers various analytics from across the platform.
    """
    # 1. Total Users: Counts every row in the 'users' table.
    # SQL equivalent: SELECT COUNT(id) FROM users;
    total_users = db.query(func.count(models.User.id)).scalar()

    # 2. Total Agents: Counts every row in the 'agents' table.
    # SQL equivalent: SELECT COUNT(id) FROM agents;
    total_agents = db.query(func.count(models.Agent.id)).scalar()

    # 3. Total Messages: Counts every row in the 'chat_messages' table.
    # SQL equivalent: SELECT COUNT(id) FROM chat_messages;
    total_messages = db.query(func.count(models.ChatMessage.id)).scalar()
    
    # 4. Average Response Time:
    # SQL equivalent: SELECT AVG(response_time_seconds) FROM chat_messages WHERE role = 'ai';
    avg_response_time = db.query(func.avg(models.ChatMessage.response_time_seconds))\
        .filter(models.ChatMessage.role == 'ai', models.ChatMessage.response_time_seconds.isnot(None))\
        .scalar()
        
    # 5. Total Tokens Used:
    # This is a two-step process for database compatibility.
    # Step 5a: Get all the JSON objects containing token usage for AI messages.
    token_usage_results = db.query(models.ChatMessage.token_usage)\
        .filter(models.ChatMessage.role == 'ai', models.ChatMessage.token_usage.isnot(None))\
        .all()
        
    # Step 5b: Sum the 'total_tokens' value from each JSON object in Python.
    total_tokens = 0
    if token_usage_results:
        for usage in token_usage_results:
            # usage[0] is the JSON object, e.g., {"total_tokens": 120}
            if usage[0] and 'total_tokens' in usage[0]:
                total_tokens += usage[0]['total_tokens']

    # 6. Time-Series Data for a Chart (Messages over the last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    messages_last_7_days = db.query(
        func.date(models.ChatMessage.timestamp).label('date'), # Group by day, not by second
        func.count(models.ChatMessage.id).label('count')      # Count messages per day
    ).filter(
        models.ChatMessage.timestamp >= seven_days_ago       # Only from the last week
    ).group_by(
        func.date(models.ChatMessage.timestamp)              # The aggregation key
    ).order_by(
        func.date(models.ChatMessage.timestamp)              # Order chronologically
    ).all()

    # 7. Format the time-series data into a clean list of objects for the frontend chart.
    time_series_data = [
        {"date": result.date.strftime("%Y-%m-%d"), "messages": result.count}
        for result in messages_last_7_days
    ]

    # 8. Return everything in a single, well-structured dictionary.
    return {
        "total_users": total_users,
        "total_agents": total_agents,
        "total_messages": total_messages,
        "avg_response_time": float(avg_response_time) if avg_response_time else 0,
        "total_tokens_used": total_tokens,
        "messages_time_series": time_series_data
    }