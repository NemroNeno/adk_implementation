from fastapi import APIRouter

from .endpoints import login, users, agents, tools, subscriptions, webhooks, admin, plans, auth, integrations # <-- ADD integrations

api_router = APIRouter()

api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# --- THIS IS THE FIX ---
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
# --- END OF FIX ---s