from fastapi import APIRouter

from app.api.v1.endpoints import login, users, agents, auth, tools, admin, subscriptions, webhooks, integrations,plans
api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
# The prefix is /auth, and the endpoint is /auth/google, so the full path is /auth/auth/google
api_router.include_router(auth.router, prefix="/auth", tags=["auth"]) 
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])

# ...
api_router.include_router(tools.router, prefix="/tools", tags=["tools"]) # Add this line
# ...
# ... (existing imports) ...
from app.api.v1.endpoints import admin # Add admin

# ...
api_router.include_router(admin.router, prefix="/admin", tags=["admin"]) # Add this line
# ...


# ...
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
# api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
# ...


# ...
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
# ... # Add plans

# ...
api_router.include_router(plans.router, prefix="/plans", tags=["plans"]) # Add this line
# ...