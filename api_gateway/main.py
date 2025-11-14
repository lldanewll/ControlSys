from fastapi import FastAPI

app = FastAPI(title="API Gateway", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "Gateway is running"}