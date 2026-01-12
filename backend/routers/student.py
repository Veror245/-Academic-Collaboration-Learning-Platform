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
from backend.services.models import Comment, Rating
from backend.services.schemas import ChatRequest, CommentCreate, UserProfileResponse, VoteCreate, RatingCreate



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
def get_room_resources(
    room_slug: str, 
    user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
):
    # A. Find Room
    room = db.query(models.Room).filter(models.Room.slug == room_slug).first()
    
    if not room:
        raise HTTPException(404, detail="Room not found")

    # B. Fetch Resources with Uploader Name
    results = (
        db.query(models.Resource, models.User.full_name)
        .join(models.User, models.Resource.uploader_id == models.User.id)
        .filter(models.Resource.room_id == room.id)
        .order_by(models.Resource.created_at.desc())
        .all()
    )
    
    # C. Format the output + Add RATING Data
    final_output = []
    
    for resource, full_name in results:
        # 1. Calculate Average Rating (Avg of 1-5 stars)
        avg_stars = db.query(func.avg(models.Rating.stars))\
            .filter(models.Rating.resource_id == resource.id)\
            .scalar()
            
        # Handle "None" if no one has rated it yet
        final_average = round(avg_stars, 1) if avg_stars else 0.0

        # 2. Check if the CURRENT user has rated this file
        existing_rating = db.query(models.Rating).filter(
            models.Rating.resource_id == resource.id,
            models.Rating.user_id == user.id
        ).first()
        
        # Get their stars (e.g., 5) or 0 if they haven't rated
        current_user_stars = existing_rating.stars if existing_rating else 0

        final_output.append({
            "id": resource.id,
            "title": resource.title,
            "file_path": resource.file_path,
            "tags": resource.tags,
            "ai_summary": resource.ai_summary,
            "uploader": full_name,
            "created_at": resource.created_at,
            # --- REPLACED FIELDS ---
            "average_rating": final_average,    # Send e.g. 4.2 to frontend
            "user_rating": current_user_stars   # Send e.g. 5 to frontend (for coloring stars)
        })

    return final_output
    

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


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # 1. Get all resources uploaded by this user
    my_uploads = db.query(models.Resource).filter(
        models.Resource.uploader_id == user.id
    ).order_by(models.Resource.created_at.desc()).all()
    
    # 2. Calculate "Karma" (Total STARS received on MY notes)
    total_karma = 0
    for resource in my_uploads:
        # Get sum of STARS for this specific resource
        # FIX: Changed from models.Vote.value to models.Rating.stars
        score = db.query(func.sum(models.Rating.stars)).filter(
            models.Rating.resource_id == resource.id
        ).scalar() 
        
        if score:
            total_karma += score

    # 3. Return the formatted profile
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": getattr(user, "role", "student"),
        "karma_score": total_karma,
        "uploads": [
            {
                "id": res.id,
                "filename": res.title, # Ensure your Pydantic model expects 'filename', or change this to 'title'
                "created_at": res.created_at
            }
            for res in my_uploads
        ]
    }


@router.post("/rate")
def rate_resource(
    rate_data: RatingCreate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if not (1 <= rate_data.stars <= 5): # <--- FIX: Use .stars from schema
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    # 1. Check if interaction row exists
    existing_interaction = db.query(models.Rating).filter(
        models.Rating.user_id == user.id,
        models.Rating.resource_id == rate_data.resource_id
    ).first()

    if existing_interaction:
        # Update existing row
        existing_interaction.stars = rate_data.stars # <--- FIX: Use .stars
    else:
        # Create new row
        new_interaction = models.Rating(
            user_id=user.id,
            resource_id=rate_data.resource_id,
            stars=rate_data.stars, # <--- FIX: Use .stars
            value=0 
        )
        db.add(new_interaction)

    db.commit()

    # 2. Calculate New Average Rating
    stats = db.query(
        func.avg(models.Rating.stars), # <--- FIX: Use .stars
        func.count(models.Rating.stars)
    ).filter(
        models.Rating.resource_id == rate_data.resource_id,
        models.Rating.stars > 0 
    ).first()

    new_average = float(stats[0]) if stats[0] else 0.0 # type: ignore
    total_ratings = stats[1] if stats[1] else 0 # type: ignore

    return {
        "msg": "Rating updated", 
        "new_average": round(new_average, 1),
        "total_ratings": total_ratings
    }