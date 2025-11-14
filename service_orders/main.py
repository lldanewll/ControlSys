from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from .database_config import get_db, create_tables
from .database import Order

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield

app = FastAPI(title="Orders Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "Orders service is running"}

@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    order_count = db.query(Order).count()
    return {"order_count": order_count, "database_status": "connected"}