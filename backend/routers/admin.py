from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.services import auth, models, database, crud

# Dependency: Block anyone who is NOT an admin
def require_admin(user: models.User = Depends(auth.get_current_user)):
    if user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admins only")
    return user

router = APIRouter(
    prefix="/admin", 
    tags=["Admin Tools"], 
    dependencies=[Depends(require_admin)] # Protects all endpoints below
)


@router.put("/verify-comment/{comment_id}")
def verify_comment(comment_id: int, db: Session = Depends(database.get_db)):
    """Only Admins can mark a student's answer as 'Verified'"""
    # Logic to fetch comment and set is_verified = True
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(404, "Comment not found")
    
    comment.is_verified = True
    db.commit()
    return {"status": "Comment Verified"}

@router.delete("/delete-resource/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(database.get_db)):
    """Admin moderation tool"""
    # Logic to delete file
    return {"status": "Deleted"}