from fastapi import FastAPI
from backend.routers import auth, admin, student
from backend.services import models, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(student.router)

@app.get("/")
def read_root():
    return {"msg": "Welcome to the Academic Collaboration and Learning Platform API"}

