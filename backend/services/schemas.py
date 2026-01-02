from pydantic import BaseModel, EmailStr
from typing import Optional
from backend.services.models import UserRole # Import your Enum

# 1. Schema for Registration (Input)
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole 
# 2. Schema for Response (Output) - Hides the password!
class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    
    class Config:
        from_attributes = True