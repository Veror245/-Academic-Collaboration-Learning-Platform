from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.services import database, auth, models
from pydantic import BaseModel
from typing import List
from datetime import datetime
import shutil
import os
from backend.services.schemas import GroupCreate, MessageCreate, MessageResponse

router = APIRouter(prefix="/groups", tags=["Study Groups"])


# --- 1. GROUP MANAGEMENT ---

@router.post("/create")
def create_group(
    group: GroupCreate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Check duplicate name
    if db.query(models.StudyGroup).filter(models.StudyGroup.name == group.name).first():
        raise HTTPException(400, "Group name already taken")
        
    new_group = models.StudyGroup(
        name=group.name,
        description=group.description,
        creator_id=user.id
    )
    # Auto-join the creator
    new_group.members.append(user)
    
    db.add(new_group)
    db.commit()
    return {"msg": "Group created!", "id": new_group.id}

@router.get("/all")
def get_all_groups(db: Session = Depends(database.get_db)):
    # Returns list of groups with member count
    groups = db.query(models.StudyGroup).all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "member_count": len(g.members)
        }
        for g in groups
    ]

@router.post("/{group_id}/join")
def join_group(
    group_id: int,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    group = db.query(models.StudyGroup).filter(models.StudyGroup.id == group_id).first()
    if not group:
        raise HTTPException(404, "Group not found")
        
    if user in group.members:
        return {"msg": "Already a member"}
        
    group.members.append(user)
    db.commit()
    return {"msg": f"Joined {group.name}!"}

@router.get("/{group_id}/members")
def get_group_members(
    group_id: int,
    db: Session = Depends(database.get_db)
):
    group = db.query(models.StudyGroup).filter(models.StudyGroup.id == group_id).first()
    if not group:
        raise HTTPException(404, "Group not found")
        
    return [
        {
            "id": m.id,
            "name": m.full_name,
            "role": "Host" if m.id == group.creator_id else "Member"
        }
        for m in group.members
    ]

# --- 2. CHAT FUNCTIONALITY ---

@router.post("/{group_id}/chat")
def send_message(
    group_id: int,
    msg: MessageCreate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    new_msg = models.Message(
        content=msg.content,
        user_id=user.id,
        group_id=group_id
    )
    db.add(new_msg)
    db.commit()
    return {"msg": "Sent"}

@router.get("/{group_id}/messages", response_model=List[MessageResponse])
def get_chat_history(
    group_id: int,
    db: Session = Depends(database.get_db)
):
    msgs = db.query(models.Message)\
        .filter(models.Message.group_id == group_id)\
        .order_by(models.Message.timestamp.asc())\
        .limit(50)\
        .all()
        
    return [
        {
            "id": m.id,
            "user_name": m.user.full_name,
            "content": m.content,
            "timestamp": m.timestamp
        }
        for m in msgs
    ]

# --- 3. RESOURCE SHARING (GROUP) ---

UPLOAD_DIR = "static/uploads" # Ensure this folder exists

@router.post("/{group_id}/upload")
def upload_group_resource(
    group_id: int,
    file: UploadFile = File(...),
    title: str = Form(...),
    tags: str = Form(""),
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Verify Group
    group = db.query(models.StudyGroup).filter(models.StudyGroup.id == group_id).first()
    if not group:
        raise HTTPException(404, "Group not found")

    # Save File
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create Resource
    new_resource = models.Resource(
        title=title,
        file_path=file_location,
        tags=tags,
        uploader_id=user.id,
        group_id=group.id,  # Linked to Group
        room_id=None,       # Public room is None
        ai_summary="Processing..." 
    )
    
    db.add(new_resource)
    db.commit()
    
    return {"msg": "File uploaded to group", "id": new_resource.id}

@router.get("/{group_id}/resources")
def get_group_resources(
    group_id: int,
    db: Session = Depends(database.get_db)
):
    resources = db.query(models.Resource)\
        .filter(models.Resource.group_id == group_id)\
        .order_by(models.Resource.created_at.desc())\
        .all() #type: ignore
        
    return [
        {
            "id": r.id,
            "title": r.title,
            "filename": os.path.basename(r.file_path),
            "uploader": r.uploader.full_name,
            "created_at": r.created_at
        }
        for r in resources
    ]