from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import httpx
import os
from jose import JWTError, jwt
from typing import Optional, List

# Настройки
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://service_users:8001")
ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL", "http://service_orders:8002")
JWT_SECRET = os.getenv("JWT_SECRET", "eANno-EM-Li4tPzYFOLS-A9khJO-FhKjCZucrVFVyIo")

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="API Gateway",
    version="1.0.0",
    lifespan=lifespan
)

# JWT утилиты
def verify_jwt_token(token: str) -> Optional[dict]:
    """Проверяет JWT токен"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Зависимость для проверки JWT"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    payload = verify_jwt_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return payload

# Проксирование запросов
async def proxy_request(
    service_url: str,
    path: str,
    method: str = "GET",
    data: Optional[dict] = None,
    headers: Optional[dict] = None
):
    """Проксирует запрос к микросервису"""
    url = f"{service_url}{path}"
    
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = await client.put(url, json=data, headers=headers)
            elif method.upper() == "PATCH":
                response = await client.patch(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Method not supported"}
                )
            
            # Проксируем ответ от сервиса
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
            
        except httpx.ConnectError:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"error": "Service unavailable"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": f"Internal server error: {str(e)}"}
            )

# Public endpoints (без аутентификации)
@app.post("/v1/register")
async def register_user(request: Request):
    """Регистрация пользователя"""
    body = await request.json()
    return await proxy_request(USERS_SERVICE_URL, "/v1/register", "POST", body)

@app.post("/v1/login")
async def login_user(request: Request):
    """Вход пользователя"""
    body = await request.json()
    return await proxy_request(USERS_SERVICE_URL, "/v1/login", "POST", body)

# Protected endpoints (требуют аутентификации)
@app.get("/v1/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Получение профиля пользователя"""
    headers = {"Authorization": f"Bearer {current_user}"}
    return await proxy_request(USERS_SERVICE_URL, "/v1/profile", "GET", headers=headers)

@app.put("/v1/profile")
async def update_user_profile(request: Request, current_user: dict = Depends(get_current_user)):
    """Обновление профиля пользователя"""
    body = await request.json()
    headers = {"Authorization": f"Bearer {current_user}"}
    return await proxy_request(USERS_SERVICE_URL, "/v1/profile", "PUT", body, headers)

@app.get("/v1/admin/users")
async def get_users_list(current_user: dict = Depends(get_current_user)):
    """Список пользователей (только для админов)"""
    headers = {"Authorization": f"Bearer {current_user}"}
    return await proxy_request(USERS_SERVICE_URL, "/v1/admin/users", "GET", headers=headers)

# Orders endpoints (требуют аутентификации)
@app.post("/v1/orders")
async def create_order(request: Request, current_user: dict = Depends(get_current_user)):
    """Создание заказа"""
    body = await request.json()
    headers = {"Authorization": f"Bearer {current_user}"}
    return await proxy_request(ORDERS_SERVICE_URL, "/v1/orders", "POST", body, headers)

@app.get("/v1/orders/{order_id}")
async def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    """Получение заказа по ID"""
    headers = {"Authorization": f"Bearer {current_user}"}
    return await proxy_request(ORDERS_SERVICE_URL, f"/v1/orders/{order_id}", "GET", headers=headers)

@app.get("/v1/orders")
async def get_orders_list(
    current_user: dict = Depends(get_current_user),
    page: int = 1,
    limit: int = 10,
    status: str = None
):
    """Список заказов пользователя"""
    params = f"?page={page}&limit={limit}"
    if status:
        params += f"&status={status}"
    
    headers = {"Authorization": f"Bearer {current_user}"}
    return await proxy_request(ORDERS_SERVICE_URL, f"/v1/orders{params}", "GET", headers=headers)

@app.patch("/v1/orders/{order_id}/status")
async def update_order_status(order_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """Обновление статуса заказа"""
    body = await request.json()
    headers = {"Authorization": f"Bearer {current_user}"}
    return await proxy_request(ORDERS_SERVICE_URL, f"/v1/orders/{order_id}/status", "PATCH", body, headers)

@app.patch("/v1/orders/{order_id}/cancel")
async def cancel_order(order_id: str, current_user: dict = Depends(get_current_user)):
    """Отмена заказа"""
    headers = {"Authorization": f"Bearer {current_user}"}
    return await proxy_request(ORDERS_SERVICE_URL, f"/v1/orders/{order_id}/cancel", "PATCH", headers=headers)

# Health checks
@app.get("/health")
async def health_check():
    """Health check gateway"""
    return {"status": "API Gateway is running"}

@app.get("/services/health")
async def services_health_check():
    """Health check всех сервисов"""
    services_status = {}
    
    async with httpx.AsyncClient() as client:
        # Проверяем users service
        try:
            response = await client.get(f"{USERS_SERVICE_URL}/health")
            services_status["users_service"] = response.status_code == 200
        except:
            services_status["users_service"] = False
        
        # Проверяем orders service
        try:
            response = await client.get(f"{ORDERS_SERVICE_URL}/health")
            services_status["orders_service"] = response.status_code == 200
        except:
            services_status["orders_service"] = False
    
    return {
        "gateway": True,
        "services": services_status
    }

@app.get("/")
async def root():
    return {"message": "Construction Control System API Gateway", "version": "1.0.0"}