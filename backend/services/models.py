import enum
from sqlalchemy import String, Text, ForeignKey, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase
from datetime import datetime, timezone
from backend.services.database import Base
from typing import List, Optional

class UserRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String)
    password_hash: Mapped[str] = mapped_column(String)
    
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole))
    
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    
    uploads: Mapped[List["Resource"]] = relationship(back_populates="uploader")
    comments: Mapped[List["Comment"]] = relationship(back_populates="user")
    tokens: Mapped[List["Token"]] = relationship(back_populates="user")

# Active Login Tokens
class Token(Base):
    __tablename__ = "tokens"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    access_token: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="tokens")

# Rooms 
class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    slug: Mapped[str] = mapped_column(String, unique=True)

    resources: Mapped[List["Resource"]] = relationship(back_populates="room")

# Resources 
class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    tags: Mapped[str] = mapped_column(String)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    
    uploader_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))

    uploader: Mapped["User"] = relationship(back_populates="uploads")
    room: Mapped["Room"] = relationship(back_populates="resources")
    comments: Mapped[List["Comment"]] = relationship(back_populates="resource")

# Comments 
class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"))

    user: Mapped["User"] = relationship(back_populates="comments")
    resource: Mapped["Resource"] = relationship(back_populates="comments")