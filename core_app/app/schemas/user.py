from pydantic import BaseModel, EmailStr

class UserSafe(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    roles: list[str] = []
    permissions: list[str] = []
    verified: bool = False
