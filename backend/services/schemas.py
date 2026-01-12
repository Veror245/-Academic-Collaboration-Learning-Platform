from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Optional
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


class ChatRequest(BaseModel):
    resource_id: int
    question: str
    # New Field: A list of previous messages 
    # Format: [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    history: List[Dict[str, str]] = []

class CommentCreate(BaseModel):
    resource_id: int
    content: str

class VoteCreate(BaseModel):
    resource_id: int
    vote_type: int # 1 = Upvote, -1 = Downvote

class MyUploadResponse(BaseModel):
    id: int
    filename: str
    created_at: datetime

# The Main Profile Response
class UserProfileResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    karma_score: int # Total upvotes received
    uploads: List[MyUploadResponse]

class RatingCreate(BaseModel):
    resource_id: int
    stars: int  # 1 to 5