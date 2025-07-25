# ... (existing imports) ...
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.oauth import oauth
from app.core.security import create_access_token
from app.db.base import get_db
from app.db.models import User as UserModel, UserRole
from app.services.audit_service import log_activity  # <-- Added import

router = APIRouter()


@router.get('/login/google')
async def login_via_google(request: Request):
    """
    Starts the Google OAuth2 login flow.
    """
    redirect_uri = request.url_for('auth_callback', provider='google')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get('/auth/{provider}', name='auth_callback')
async def auth_callback(request: Request, provider: str, db: Session = Depends(get_db)):
    """
    Callback endpoint for OAuth providers like Google.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not authorize with Google")

    user_info = token.get('userinfo')
    if not user_info or not user_info.get('email'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not retrieve user info from Google")

    email = user_info['email']
    user = db.query(UserModel).filter(UserModel.email == email).first()

    if not user:
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

    # --- LOG THE SUCCESSFUL OAUTH LOGIN ---
    log_activity(
        db,
        action=f"USER_LOGIN_OAUTH_{provider.upper()}",
        user_id=user.id,
        details={"provider": provider}
    )

    # Generate access token
    access_token = create_access_token(data={"sub": user.email})
    
    # Redirect to frontend with token
    return RedirectResponse(url=f"http://localhost:3000/auth/callback?token={access_token}")
