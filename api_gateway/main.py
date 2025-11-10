from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import os

app = FastAPI()

USERS_SERVICE_URL = os.environ.get("USERS_SERVICE_URL", "http://service_users:8000")
ORDERS_SERVICE_URL = os.environ.get("ORDERS_SERVICE_URL", "http://service_orders:8000")

# Проксирующие эндпоинты для users
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{USERS_SERVICE_URL}/users/{user_id}")
    if r.status_code == 404:
        return JSONResponse(status_code=404, content={"error": "User not found"})
    return r.json()

@app.post("/users", status_code=201)
async def create_user(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{USERS_SERVICE_URL}/users", json=body)
    return r.json()

@app.get("/users")
async def get_users():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{USERS_SERVICE_URL}/users")
    return r.json()

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{USERS_SERVICE_URL}/users/{user_id}")
    return r.json()

@app.put("/users/{user_id}")
async def update_user(user_id: int, request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.put(f"{USERS_SERVICE_URL}/users/{user_id}", json=body)
    return r.json()

# Проксирующие эндпоинты для orders
@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{ORDERS_SERVICE_URL}/orders/{order_id}")
    if r.status_code == 404:
        return JSONResponse(status_code=404, content={"error": "Order not found"})
    return r.json()

@app.post("/orders", status_code=201)
async def create_order(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{ORDERS_SERVICE_URL}/orders", json=body)
    return r.json()

@app.get("/orders")
async def get_orders():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{ORDERS_SERVICE_URL}/orders")
    return r.json()

@app.delete("/orders/{order_id}")
async def delete_order(order_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{ORDERS_SERVICE_URL}/orders/{order_id}")
    return r.json()

@app.put("/orders/{order_id}")
async def update_order(order_id: int, request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        r = await client.put(f"{ORDERS_SERVICE_URL}/orders/{order_id}", json=body)
    return r.json()

@app.get("/orders/status")
async def orders_status():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{ORDERS_SERVICE_URL}/orders/status")
    return r.json()

@app.get("/orders/health")
async def orders_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{ORDERS_SERVICE_URL}/orders/health")
    return r.json()

@app.get("/users/{user_id}/details")
async def user_details(user_id: int):
    async with httpx.AsyncClient() as client:
        user_req = client.get(f"{USERS_SERVICE_URL}/users/{user_id}")
        orders_req = client.get(f"{ORDERS_SERVICE_URL}/orders")
        user, orders = await httpx.AsyncClient.gather(user_req, orders_req)
    if user.status_code == 404:
        return JSONResponse(status_code=404, content={"error": "User not found"})
    user_data = user.json()
    orders = [o for o in orders.json() if o.get("userId") == user_id]
    return {"user": user_data, "orders": orders}

@app.get("/health")
async def gateway_health():
    return {"status": "API Gateway is running"}

@app.get("/status")
async def gateway_status():
    return {"status": "API Gateway is running"}
