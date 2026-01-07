import shutil
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.services import database, models, auth
from backend.services import ai_services
from pydantic import BaseModel 
from backend.services.models import Comment, Vote


#Define the Input Format
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

router = APIRouter(prefix="/student", tags=["Student Features"])

UPLOAD_DIR = "static/uploads"

# --- 1. UPLOAD ENDPOINT ---
@router.post("/upload")
def upload_resource(
    title: str = Form(...),
    room_slug: str = Form(...),  # e.g., "cs", "physics"
    tags: str = Form(...),       # e.g., "Notes, Exam"
    file: UploadFile = File(...),
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # A. Validate File Type
    if file.content_type != "application/pdf":
        raise HTTPException(400, detail="Only PDF files are allowed")

    room = db.query(models.Room).filter(models.Room.slug == room_slug).first()
    
    if not room:
        raise HTTPException(404, detail="Invalid Study Room")
    
    room_folder = os.path.join(UPLOAD_DIR, room_slug)
    
    # Create the folder if it doesn't exist yet
    os.makedirs(room_folder, exist_ok=True)

    # C. Save File Locally
    timestamp = int(datetime.now(timezone.utc).timestamp())
    clean_filename = f"{timestamp}_{file.filename.replace(' ', '_')}" # type: ignore
    file_path = os.path.join(room_folder, clean_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # D. Save Entry to Database
    new_resource = models.Resource(
        title=title,
        file_path=f"static/uploads/{room_slug}/{clean_filename}", # Relative path for frontend
        tags=tags,
        uploader_id=user.id,
        room_id=room.id,
        ai_summary="Pending..." 
    )

    db.add(new_resource)
    db.commit()
    db.refresh(new_resource)
    
    try:
        # 1. Run the AI processing (This might take 3-5 seconds)
        summary = ai_services.process_document(file_path, new_resource.id)
        
        # 2. Update the database with the real summary
        new_resource.ai_summary = summary # type: ignore
        db.commit()
        
    except Exception as e:
        print(f"AI Error: {e}")
        new_resource.ai_summary = "Summary generation failed."
        db.commit()

    return {"msg": "Upload successful", "resource_id": new_resource.id, "summary": new_resource.ai_summary}

# 2. LIST FILES ENDPOINT
@router.get("/room/{room_slug}/resources")
def get_room_resources(room_slug: str, db: Session = Depends(database.get_db)):
    # A. Find Room (Legacy Style)
    room = db.query(models.Room).filter(models.Room.slug == room_slug).first()
    
    if not room:
        raise HTTPException(404, detail="Room not found")

    # B. Fetch Resources with Uploader Name (Legacy Style)
    # Logic: Query Resource and User.full_name, Join them, Filter by Room
    results = (
        db.query(models.Resource, models.User.full_name)
        .join(models.User, models.Resource.uploader_id == models.User.id)
        .filter(models.Resource.room_id == room.id)
        .order_by(models.Resource.created_at.desc())
        .all()
    )
    
    # Format the output cleanly
    # In legacy query, 'results' is a list of tuples: (ResourceObject, "John Doe")
    return [
        {
            "id": resource.id,
            "title": resource.title,
            "file_path": resource.file_path,
            "tags": resource.tags,
            "ai_summary": resource.ai_summary,
            "uploader": full_name,  # Extracted from the join
            "created_at": resource.created_at
        }
        for resource, full_name in results
    ]
    

@router.post("/chat")
def chat_with_resource(
    chat_data: ChatRequest,
    user: models.User = Depends(auth.get_current_user),
):
    try:
        # Pass the history list to the function
        answer = ai_services.chat_with_document(
            chat_data.resource_id, 
            chat_data.question, 
            chat_data.history
        )
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/quiz/{resource_id}")
def get_quiz(resource_id: int, user: models.User = Depends(auth.get_current_user)):
    try:
        quiz = ai_services.generate_quiz(resource_id)
        return {"quiz": quiz}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comment")
def add_comment(
    comment_data: CommentCreate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    new_comment = models.Comment(
        content=comment_data.content,
        user_id=user.id,
        resource_id=comment_data.resource_id,
        is_verified=False
    )
    db.add(new_comment)
    db.commit()
    return {"msg": "Comment added!"}

@router.get("/comments/{resource_id}")
def get_comments(resource_id: int, db: Session = Depends(database.get_db)):
    results = (
        db.query(models.Comment, models.User.full_name)
        .join(models.User, models.Comment.user_id == models.User.id)
        .filter(models.Comment.resource_id == resource_id)
        
        # --- THE SORTING MAGIC ---
        # 1. Verified comments FIRST (True > False)
        # 2. Then Newest comments (created_at DESC)
        .order_by(models.Comment.is_verified.desc(), models.Comment.created_at.desc())
        # -------------------------
        
        .all()
    )
    
    return [
        {
            "id": c.id,
            "text": c.content,
            "user": user_name,
            "is_verified": c.is_verified,
            "created_at": c.created_at
        }
        for c, user_name in results
    ]

@router.post("/vote")
def vote_resource(
    vote_data: VoteCreate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # 1. Check if user already voted on this file
    existing_vote = db.query(models.Vote).filter(
        models.Vote.user_id == user.id,
        models.Vote.resource_id == vote_data.resource_id
    ).first()

    if existing_vote:
        # 2. Logic: If clicking the SAME button -> Remove Vote (Toggle Off)
        if existing_vote.value == vote_data.vote_type:
            db.delete(existing_vote)
            msg = "Vote removed"
        else:
            # 3. Logic: If clicking DIFFERENT button -> Switch Vote (Up to Down)
            existing_vote.value = vote_data.vote_type
            msg = "Vote updated"
    else:
        # 4. Logic: New Vote
        new_vote = models.Vote(
            user_id=user.id,
            resource_id=vote_data.resource_id,
            value=vote_data.vote_type
        )
        db.add(new_vote)
        msg = "Vote added"

    db.commit()
    
    # 5. Return the new Total Score instantly (for UI updates)
    total_score = db.query(func.sum(models.Vote.value)).filter(
        models.Vote.resource_id == vote_data.resource_id
    ).scalar() or 0
    
    return {"msg": msg, "new_score": total_score}

@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # 1. Get all resources uploaded by this user
    my_uploads = db.query(models.Resource).filter(
        models.Resource.uploader_id == user.id
    ).order_by(models.Resource.created_at.desc()).all()
    
    # 2. Calculate "Karma" (Total upvotes received on MY notes)
    # We loop through uploads and sum the votes for each.
    total_karma = 0
    for resource in my_uploads:
        # Get sum of votes for this specific resource
        score = db.query(func.sum(models.Vote.value)).filter(
            models.Vote.resource_id == resource.id
        ).scalar() # .scalar() returns the single number (or None)
        
        if score:
            total_karma += score

    # 3. Return the formatted profile
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": getattr(user, "role", "student"), # Fallback if 'role' column doesn't exist yet
        "karma_score": total_karma,
        "uploads": [
            {
                "id": res.id,
                "filename": res.title,
                "created_at": res.created_at
            }
            for res in my_uploads
        ]
    }