import sys
import os
import random
from datetime import datetime, timedelta, timezone

# Add Project Root to System Path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir) 

from sqlalchemy.orm import Session
from backend.services.database import SessionLocal, engine, Base
from backend.services import models, auth

# CONFIGURATION
NUM_USERS = 5
NUM_RESOURCES = 50
NUM_RATINGS = 40

def populate():
    # 1. Init Database
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    print("🔌 Connected to Database...")

    try:
        # --- 1. CREATE USERS ---
        print("👤 Creating users...")
        users = []
        for i in range(NUM_USERS):
            email = f"student{i}@test.com"
            existing = db.query(models.User).filter(models.User.email == email).first()
            
            if existing:
                users.append(existing)
            else:
                new_user = models.User(
                    email=email,
                    full_name=f"Student {i}",
                    password_hash=auth.hash_password("password123"), 
                    role=models.UserRole.STUDENT, 
                    last_login=datetime.now(timezone.utc)
                )
                db.add(new_user)
                users.append(new_user)
        
        db.commit() 
        for u in users: db.refresh(u) 

        # --- 2. CREATE ROOMS ---
        print("🏫 Checking rooms...")
        room_slugs = ["cs", "ece", "mech", "civil", "science", "hum"]
        rooms = []
        for slug in room_slugs:
            room = db.query(models.Room).filter(models.Room.slug == slug).first()
            if not room:
                room = models.Room(name=slug.upper(), slug=slug)
                db.add(room)
            rooms.append(room)
        db.commit()
        # Refresh to get IDs
        for r in rooms: db.refresh(r)

        # --- 3. CREATE RESOURCES ---
        print("📄 Generating backdated uploads...")
        resources = []
        for _ in range(NUM_RESOURCES):
            days_ago = random.randint(0, 7)
            fake_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
            
            uploader = random.choice(users)
            room = random.choice(rooms) 

            res = models.Resource(
                title=f"Notes for Subject {random.randint(101, 999)}",
                file_path="fake/path.pdf",
                tags="notes,pdf,important",
                ai_summary="This is a generated summary for testing.",
                uploader_id=uploader.id,
                room_id=room.id,
                created_at=fake_date 
            )
            db.add(res)
            resources.append(res)
        
        db.commit()
        for r in resources: db.refresh(r)

        # --- 4. ADD RATINGS (FIXED LOGIC) ---
        print("⭐ Adding ratings...")
        
        # Track pairs we've already added in this session to prevent duplicates
        seen_pairs = set()
        
        count = 0
        max_retries = NUM_RATINGS * 2 # Safety break
        
        while count < NUM_RATINGS and max_retries > 0:
            user = random.choice(users)
            res = random.choice(resources)
            pair = (user.id, res.id)
            
            # 1. Skip if we just decided to add this pair a second ago
            if pair in seen_pairs:
                max_retries -= 1
                continue

            # 2. Skip if it's already in the DB (from a previous run)
            db_exists = db.query(models.Rating).filter(
                models.Rating.user_id == user.id, 
                models.Rating.resource_id == res.id
            ).first()

            if db_exists:
                seen_pairs.add(pair)
                max_retries -= 1
                continue

            # 3. Add Valid Rating
            rating = models.Rating(
                user_id=user.id,
                resource_id=res.id,
                stars=random.randint(3, 5),
                value=0
            )
            db.add(rating)
            seen_pairs.add(pair)
            count += 1

        db.commit()
        print("✅ Success! Database populated correctly.")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate()