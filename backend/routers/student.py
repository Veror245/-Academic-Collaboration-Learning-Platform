import shutil
import os
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from backend.services import database, models, auth
from backend.services import ai_services
from pydantic import BaseModel 


#Define the Input Format
class ChatRequest(BaseModel):
    resource_id: int
    question: str

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

    # C. Save File Locally
    timestamp = int(datetime.now(timezone.utc).timestamp())
    clean_filename = f"{timestamp}_{file.filename.replace(' ', '_')}" # type: ignore
    file_path = os.path.join(UPLOAD_DIR, clean_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # D. Save Entry to Database
    new_resource = models.Resource(
        title=title,
        file_path=f"static/uploads/{clean_filename}", # Relative path for frontend
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
    user: models.User = Depends(auth.get_current_user), # Only logged-in users can chat
):
    try:
        # Call the AI service
        answer = ai_services.chat_with_document(chat_data.resource_id, chat_data.question)
        
        return {"answer": answer}
        
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate answer")
    

@router.post("/quiz/{resource_id}")
def get_quiz(resource_id: int, user: models.User = Depends(auth.get_current_user)):
    try:
        quiz = ai_services.generate_quiz(resource_id)
        return {"quiz": quiz}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))