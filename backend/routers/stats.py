from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.services import database, models, auth
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/stats", tags=["Analytics"])

@router.get("/dashboard")
def get_dashboard_stats(
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # --- 1. METRICS ---
    # Total Counts
    total_resources = db.query(models.Resource).count()
    total_groups = db.query(models.StudyGroup).count()
    
    # Active Users (Logged in within last 24 hours)
    yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
    active_users = db.query(models.User).filter(
        models.User.last_login >= yesterday
    ).count()

    # Engagement Score (Messages + Ratings)
    msg_count = db.query(models.Message).count()
    rating_count = db.query(models.Rating).count()
    engagement_score = msg_count + rating_count

    # --- 2. CHAMPION RESOURCE (Highest Rated) ---
    # Query: Join Resource & Rating -> Group by Resource -> Sort by Avg Stars
    popular = db.query(
        models.Resource,
        func.avg(models.Rating.stars).label("avg_rating"),
        models.User.full_name
    ).join(models.Rating, models.Resource.id == models.Rating.resource_id)\
     .join(models.User, models.Resource.uploader_id == models.User.id)\
     .group_by(models.Resource.id)\
     .order_by(desc("avg_rating"))\
     .first()

    if popular:
        resource, rating, uploader_name = popular
        popular_data = {
            "title": resource.title,
            "uploader": uploader_name,
            "rating": round(rating, 1), # e.g., 4.8
            "id": resource.id
        }
    else:
        popular_data = None

    # --- 3. GRAPH DATA: Upload Trends (Last 7 Days) ---
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    # SQLite-compatible date grouping
    daily_uploads = db.query(
        func.date(models.Resource.created_at).label("date"),
        func.count(models.Resource.id).label("count")
    ).filter(
        models.Resource.created_at >= seven_days_ago
    ).group_by("date").all()

    # Prepare arrays for Chart.js
    trend_labels = [str(day.date) for day in daily_uploads]
    trend_data = [day.count for day in daily_uploads]

    # --- 4. RECENT ACTIVITY FEED ---
    recent_uploads = db.query(models.Resource).order_by(
        models.Resource.created_at.desc()
    ).limit(5).all()

    formatted_recents = [
        {
            "title": res.title,
            "user": res.uploader.full_name,
            "time": res.created_at.strftime("%H:%M")
        }
        for res in recent_uploads
    ]

    return {
        "metrics": {
            "active_users": active_users,
            "resources": total_resources,
            "groups": total_groups,
            "engagement": engagement_score
        },
        "popular_resource": popular_data,
        "chart": {
            "labels": trend_labels,
            "data": trend_data
        },
        "recent_activity": formatted_recents
    }