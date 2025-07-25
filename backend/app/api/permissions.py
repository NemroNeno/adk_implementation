from fastapi import Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_user
from app.db.models import User, UserRole, Agent
from app.db.base import get_db # <-- ADDED IMPORT for get_db
from app.core.plans import PLANS

ROLE_HIERARCHY = {
    UserRole.viewer: 1,
    UserRole.user: 2,
    UserRole.admin: 3,
}

class RoleChecker:
    def __init__(self, required_roles: List[UserRole]):
        self.required_roles = required_roles

    def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )
        return current_user

allow_user_and_admin = RoleChecker([UserRole.user, UserRole.admin])
allow_admin_only = RoleChecker([UserRole.admin])
allow_all_roles = RoleChecker([UserRole.viewer, UserRole.user, UserRole.admin])

class UsageChecker:
    def __init__(self, check_agents: bool = False, check_tokens: bool = False):
        self.check_agents = check_agents
        self.check_tokens = check_tokens

    def __call__(self, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        plan = PLANS.get(current_user.plan, PLANS["free"])
        
        if self.check_agents:
            agent_count = db.query(func.count(Agent.id)).filter(Agent.owner_id == current_user.id).scalar()
            if agent_count >= plan["limits"]["max_agents"]:
                raise HTTPException(status_code=403, detail=f"Agent limit reached for {plan['name']}. Please upgrade.")
        
        if self.check_tokens:
            if current_user.token_usage_this_month >= plan["limits"]["max_tokens_per_month"]:
                raise HTTPException(status_code=403, detail=f"Monthly token limit reached.")
                
        return current_user