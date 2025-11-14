from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="API Gateway", version="1.0.0", lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "Gateway is running"}