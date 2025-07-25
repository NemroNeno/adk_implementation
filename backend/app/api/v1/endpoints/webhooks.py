import stripe
from fastapi import APIRouter, Depends, Request, Header, HTTPException
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.base import get_db
from app.db.models import User

router = APIRouter()

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=stripe_signature, secret=settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    event_type = event['type']
    data_object = event['data']['object']
    
    if event_type == 'checkout.session.completed':
        user_id = data_object.get('client_reference_id')
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.stripe_subscription_id = data_object.get('subscription')
            user.stripe_customer_id = data_object.get('customer')
            user.plan = 'pro'
            # Also reset their token usage upon initial subscription
            user.token_usage_this_month = 0
            db.commit()
            print(f"User {user.id} successfully subscribed to Pro plan.")
            
    elif event_type == 'customer.subscription.deleted':
        user = db.query(User).filter(User.stripe_subscription_id == data_object.id).first()
        if user:
            user.plan = 'free'
            user.stripe_subscription_id = None
            db.commit()
            print(f"User {user.id} subscription canceled, downgraded to Free plan.")

    # --- ADD THIS NEW EVENT HANDLER ---
    elif event_type == 'invoice.payment_succeeded':
        # This event occurs for every successful recurring payment
        subscription_id = data_object.get('subscription')
        if subscription_id:
            user = db.query(User).filter(User.stripe_subscription_id == subscription_id).first()
            if user:
                # Reset the user's monthly token usage
                user.token_usage_this_month = 0
                db.commit()
                print(f"User {user.id} subscription renewed. Token usage reset.")
    # --- END OF NEW HANDLER ---

    return {"status": "success"}