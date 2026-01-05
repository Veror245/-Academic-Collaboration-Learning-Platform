from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.services import auth, models, database
import os

# Dependency: Block anyone who is NOT an admin
def require_admin(user: models.User = Depends(auth.get_current_user)):
    if user.role != models.UserRole.ADMIN: 
        raise HTTPException(status_code=403, detail="Admins only")
    return user

router = APIRouter(
    prefix="/admin", 
    tags=["Admin Tools"], 
    dependencies=[Depends(require_admin)] # 🔒 Protects ALL endpoints below
)

@router.put("/verify-comment/{comment_id}")
def verify_comment(comment_id: int, db: Session = Depends(database.get_db)):
    """
    Toggle: If unverified -> Verify it. If verified -> Unverify it.
    """
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(404, "Comment not found")
    
    # Toggle logic (Better UX than just setting True)
    comment.is_verified = not comment.is_verified
    db.commit()
    
    status = "Verified" if comment.is_verified else "Unverified"
    return {"status": f"Comment {status}", "is_verified": comment.is_verified}

@router.delete("/delete-resource/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(database.get_db)):
    """
    Admin moderation tool: Delete inappropriate files
    """
    resource = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    
    if not resource:
        raise HTTPException(404, "Resource not found")
        
    
    if os.path.exists(resource.file_path):
        os.remove(resource.file_path)

    db.delete(resource) # This cascades to comments/votes if models are set up right
    db.commit()
    
    return {"status": "Resource and associated data deleted"}