from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.services.database import engine, SessionLocal, get_db
from backend.services.models import Base, Room
from backend.routers import auth, admin, student, groups
from backend.services import models, database
from fastapi.staticfiles import StaticFiles
import os

models.Base.metadata.create_all(bind=database.engine)

def seed_rooms():
    db = SessionLocal()
    if db.query(Room).first():
        print("Rooms already exist. Skipping seed.")
        db.close()
        return

    print("Seeding default rooms...")
    rooms = [
        Room(name="Computer Science", slug="cs"),
        Room(name="Electronics & Comm", slug="ece"),
        Room(name="Mechanical Eng", slug="mech"),
        Room(name="Civil Engineering", slug="civil"),
        Room(name="Basic Sciences (Phy/Chem/Math)", slug="science"),
        Room(name="Management & Humanities", slug="hum"),
    ]
    
    db.add_all(rooms)
    db.commit()
    print("Rooms added successfully!")
    db.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

seed_rooms()

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 2. Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(student.router)
app.include_router(groups.router)

@app.get("/")
def read_root():
    return {"msg": "Welcome to the Academic Collaboration and Learning Platform API"}

