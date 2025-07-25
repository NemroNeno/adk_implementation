import stripe
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import get_db
from app.api.deps import get_current_user
from app.db.models import User
from app.crud import crud_user

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()

@router.post("/create-checkout-session")
def create_checkout_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    customer_id = current_user.stripe_customer_id
    if not customer_id:
        # Create a new Stripe customer
        customer = stripe.Customer.create(email=current_user.email, name=current_user.full_name)
        customer_id = customer.id
        current_user.stripe_customer_id = customer_id
        db.commit()

    try:
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': settings.STRIPE_PRO_PLAN_PRICE_ID,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='http://localhost:3000/dashboard/billing?success=true',
            cancel_url='http://localhost:3000/dashboard/billing?canceled=true',
            # This is crucial to link the session back to our user
            client_reference_id=current_user.id
        )
        return JSONResponse({"url": checkout_session.url})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create-portal-session")
def create_portal_session(
    current_user: User = Depends(get_current_user)
):
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="User is not a Stripe customer.")
        
    portal_session = stripe.billing_portal.Session.create(
        customer=current_user.stripe_customer_id,
        return_url='http://localhost:3000/dashboard/billing',
    )
    return JSONResponse({"url": portal_session.url})