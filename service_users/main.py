from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from .database_config import get_db, create_tables
from .database import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield
    pass

app = FastAPI(title="Users Service", version="1.0.0", lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "Users service is running"}

@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    user_count = db.query(User).count()
    return {"user_count": user_count, "database_status": "connected"}