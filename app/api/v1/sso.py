from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token
from app.services.sso_service import sso_service
from app.schemas.sso import SSOAuthorizeResponse
from datetime import timedelta
from app.core.config import settings

router = APIRouter()

@router.get("/authorize", response_model=SSOAuthorizeResponse)
def sso_authorize():
    if not sso_service.enabled:
        raise HTTPException(status_code=400, detail="SSO is not enabled")

    url, state = sso_service.get_authorization_url()
    return {"url": url, "state": state}

@router.get("/callback")
async def sso_callback(code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)):
    if not sso_service.enabled:
        raise HTTPException(status_code=400, detail="SSO is not enabled")

    try:
        token_data = await sso_service.exchange_code_for_token(code)
        access_token = token_data.get("access_token")

        user_info = await sso_service.get_user_info(access_token)
        user = sso_service.get_or_create_user(db, user_info)

        jwt_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        redirect_url = f"http://localhost:5173/login?token={jwt_token}"
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SSO authentication failed: {str(e)}")

@router.get("/config")
def get_sso_config():
    return {
        "enabled": sso_service.enabled,
        "provider": sso_service.provider if sso_service.enabled else None
    }