from fastapi import APIRouter, Depends
from backend.services import auth, models

router = APIRouter(prefix="/student", tags=["Student Features"])

@router.get("/dashboard")
def student_dashboard(user: models.User = Depends(auth.get_current_user)):
    return {"msg": f"Welcome, {user.full_name}. Here are your study rooms."}

# Add Upload / Chat routes here later