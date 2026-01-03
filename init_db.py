from backend.services.database import engine, SessionLocal, get_db
from backend.services.models import Base, Room

# Create tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)

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

if __name__ == "__main__":
    seed_rooms()
    print("Database initialization complete.")