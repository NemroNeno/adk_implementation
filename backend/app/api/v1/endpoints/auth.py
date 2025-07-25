from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.oauth import oauth
from app.core.security import create_access_token
from app.db.base import get_db
from app.db.models import User as UserModel, UserRole
from app.services.audit_service import log_activity

router = APIRouter()

@router.get('/login/google')
async def login_via_google(request: Request):
    """
    Starts the Google OAuth2 login flow.
    """
    # This must match the name of the endpoint function below
    redirect_uri = request.url_for('auth_callback', provider='google')
    return await oauth.google.authorize_redirect(request, redirect_uri)


# The 'name' here is critical for request.url_for to work
@router.get('/auth/{provider}', name='auth_callback')
async def auth_callback(request: Request, provider: str, db: Session = Depends(get_db)):
    """
    This is the callback URL that Google redirects to.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        print(f"!! OAUTH ERROR: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Could not authorize with Google")
    
    user_info = token.get('userinfo')
    if not user_info or not user_info.get('email'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not retrieve user info from Google")

    email = user_info['email']
    user = db.query(UserModel).filter(UserModel.email == email).first()

    if not user:
        # If user doesn't exist, create them
        new_user = UserModel(
            email=email,
            full_name=user_info.get('name'),
            provider='google',
            role=UserRole.user
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user
    
    log_activity(db, action="USER_LOGIN_OAUTH_GOOGLE", user_id=user.id)
    access_token = create_access_token(data={"sub": user.email})
    
    # Redirect the user to the frontend callback page with the token
    return RedirectResponse(url=f"http://localhost:3000/auth/callback?token={access_token}")