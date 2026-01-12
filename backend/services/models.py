import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase
from datetime import datetime, timezone
from backend.services.database import Base
from typing import List, Optional
from sqlalchemy import Table

# Association Table for Many-to-Many
group_members = Table(
    "group_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("group_id", Integer, ForeignKey("study_groups.id"), primary_key=True)
)

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
    ratings: Mapped[list["Rating"]] = relationship(back_populates="user")
    tokens: Mapped[List["Token"]] = relationship(back_populates="user")
    joined_groups: Mapped[List["StudyGroup"]] = relationship(secondary=group_members, back_populates="members")

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
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=True)

    uploader: Mapped["User"] = relationship(back_populates="uploads")
    room: Mapped["Room"] = relationship(back_populates="resources")
    comments: Mapped[list["Comment"]] = relationship(back_populates="resource", cascade="all, delete-orphan")
    ratings: Mapped[list["Rating"]] = relationship(back_populates="resource", cascade="all, delete-orphan")
    
    group: Mapped["StudyGroup"] = relationship(back_populates="resources")
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("study_groups.id"), nullable=True)

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

class Rating(Base):
    __tablename__ = "ratings"

    # Composite Primary Key (User + Resource)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"), primary_key=True)
    
    # 1 for Upvote, -1 for Downvote
    value: Mapped[int] = mapped_column(Integer, default=0)
    stars: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="ratings")
    resource: Mapped["Resource"] = relationship(back_populates="ratings")
    
class StudyGroup(Base):
    __tablename__ = "study_groups"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Relationships
    creator: Mapped["User"] = relationship("User") 
    messages: Mapped[List["Message"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    resources: Mapped[List["Resource"]] = relationship(back_populates="group")
    members: Mapped[List["User"]] = relationship(secondary=group_members, back_populates="joined_groups")

class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("study_groups.id"))
    
    user: Mapped["User"] = relationship("User")
    group: Mapped["StudyGroup"] = relationship(back_populates="messages")