import time
from authlib.jose import jwt
from fastapi import HTTPException
from backend.services.crud import get_user_by_id
from backend.services.models import User
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from backend.services.database import get_db
from passlib.context import CryptContext

SECRET_KEY = "supersecret"  
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

pwd_hash = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_token(user: User, expires_in: int = 3600):
    header = {"alg": "HS256"}
    payload = {
        "sub": user.id,
        "email": user.email,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in
    }
    token = jwt.encode(header, payload, SECRET_KEY)
    return token.decode()

def verify_token(token: str):
    try:
        claims = jwt.decode(token, SECRET_KEY)
        claims.validate()
        return claims
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

def hash_password(password: str):
    return pwd_hash.hash(password)

def verify_password(password: str, hashed_password: str):
    return pwd_hash.verify(password, hashed_password)