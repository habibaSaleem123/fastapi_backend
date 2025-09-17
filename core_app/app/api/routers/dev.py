# app/api/routers/dev.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from app.core.config.settings import settings
from app.db.models.user import User
from app.core.security.jwt import create_verify_email_token, create_reset_password_token

router = APIRouter(prefix="/dev", tags=["dev"])

class EmailIn(BaseModel):
    email: EmailStr

def require_dev():
    if (settings.ENV or "").lower() != "dev":
        raise HTTPException(status_code=403, detail="Not allowed outside dev")

@router.post("/mint-verify-token", dependencies=[Depends(require_dev)])
async def mint_verify_token(payload: EmailIn):
    user = await User.find_one(User.email == payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"token": create_verify_email_token(sub=user.id, email=user.email)}

@router.post("/mint-reset-token", dependencies=[Depends(require_dev)])
async def mint_reset_token(payload: EmailIn):
    user = await User.find_one(User.email == payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"token": create_reset_password_token(sub=user.id)}
