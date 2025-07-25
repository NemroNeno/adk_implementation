from fastapi import APIRouter
from app.core.plans import PLANS

router = APIRouter()

@router.get("/")
def get_all_plans():
    """
    Returns the details and limits of all available subscription plans.
    """
    return PLANS