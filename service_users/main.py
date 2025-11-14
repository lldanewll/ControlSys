from fastapi import FastAPI

app = FastAPI(title="Service Users", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "Service is running"}