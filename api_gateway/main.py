from fastapi import FastAPI, HTTPException, Depends, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import httpx
import os
from jose import JWTError, jwt
from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal
from pydantic import BaseModel, EmailStr
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://service_users:8001")
ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL", "http://service_orders:8002")
JWT_SECRET = os.getenv("JWT_SECRET", "eANno-EM-Li4tPzYFOLS-A9khJO-FhKjCZucrVFVyIo")

logger.info(f"JWT_SECRET in Gateway: {JWT_SECRET}")


security_scheme = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    email: EmailStr  
    name: str
    password: str
    roles: List[str] = ["engineer"]

class LoginRequest(BaseModel):
    email: EmailStr  
    password: str


class ProfileUpdateRequest(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    roles: Optional[List[str]] = None

class OrderItem(BaseModel):
    product: str
    quantity: int
    price: float

class OrderCreateRequest(BaseModel):
    items: List[OrderItem]

class OrderStatusUpdateRequest(BaseModel):
    status: Optional[str] = None

class AdminCreateRequest(BaseModel):
    email: EmailStr  
    name: str
    password: str
    roles: List[str]

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="API Gateway",
    version="1.0.0",
    lifespan=lifespan
)


def verify_jwt_token(token: str) -> Optional[dict]:
    """Проверяет JWT токен"""
    try:
        logger.info(f"Verifying token in Gateway: {token[:50]}...")
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        logger.info(f"Token payload in Gateway: {payload}")
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed in Gateway: {str(e)}")
        return None

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)):
    """Зависимость для проверки JWT"""
    if not credentials:
        logger.warning("No credentials provided to Gateway")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    logger.info(f"Received token in Gateway: {credentials.credentials[:50]}...")
    payload = verify_jwt_token(credentials.credentials)
    if not payload:
        logger.warning("Invalid or expired token in Gateway")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    logger.info("JWT token validated successfully in Gateway")
    return credentials.credentials

async def proxy_request(
    service_url: str,
    path: str,
    method: str = "GET",
    data: Optional[dict] = None,
    headers: Optional[dict] = None
):
    """Проксирует запрос к микросервису"""
    url = f"{service_url}{path}"
    
    request_headers = headers.copy() if headers else {}
    if data and method.upper() in ["POST", "PUT", "PATCH"]:
        request_headers["Content-Type"] = "application/json"
    
    async with httpx.AsyncClient() as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, headers=request_headers)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, headers=request_headers)
            elif method.upper() == "PUT":
                response = await client.put(url, json=data, headers=request_headers)
            elif method.upper() == "PATCH":
                response = await client.patch(url, json=data, headers=request_headers)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=request_headers)
            else:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Method not supported"}
                )
            
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

@app.post("/v1/register")
async def register_user(register_data: RegisterRequest):
    """Регистрация пользователя"""
    try:
        return await proxy_request(
            USERS_SERVICE_URL, 
            "/v1/register", 
            "POST", 
            register_data.dict()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/v1/login")
async def login_user(login_data: LoginRequest):
    """Вход пользователя"""
    try:
        return await proxy_request(
            USERS_SERVICE_URL, 
            "/v1/login", 
            "POST", 
            login_data.dict()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/v1/profile")
async def get_user_profile(token: str = Depends(get_current_user)):
    """Получение профиля пользователя"""
    headers = {"Authorization": f"Bearer {token}"}
    return await proxy_request(USERS_SERVICE_URL, "/v1/profile", "GET", headers=headers)

@app.put("/v1/profile")
async def update_user_profile(
    update_data: ProfileUpdateRequest, 
    token: str = Depends(get_current_user)
):
    """Обновление профиля пользователя"""
    headers = {"Authorization": f"Bearer {token}"}
    return await proxy_request(
        USERS_SERVICE_URL, 
        "/v1/profile", 
        "PUT", 
        update_data.dict(), 
        headers
    )

@app.get("/v1/admin/users")
async def get_users_list(token: str = Depends(get_current_user)):
    """Список пользователей (только для админов)"""
    headers = {"Authorization": f"Bearer {token}"}
    return await proxy_request(USERS_SERVICE_URL, "/v1/admin/users", "GET", headers=headers)

@app.post("/v1/admin/users")
async def create_user_admin(
    user_data: AdminCreateRequest,
    token: str = Depends(get_current_user)
):
    """Создание пользователя админом (с любыми ролями)"""
    headers = {"Authorization": f"Bearer {token}"}
    return await proxy_request(
        USERS_SERVICE_URL, 
        "/v1/admin/users", 
        "POST", 
        user_data.dict(), 
        headers
    )

@app.post("/v1/orders")
async def create_order(
    order_data: OrderCreateRequest,
    token: str = Depends(get_current_user)
):
    """Создание заказа"""
    headers = {"Authorization": f"Bearer {token}"}
    return await proxy_request(
        ORDERS_SERVICE_URL, 
        "/v1/orders", 
        "POST", 
        order_data.dict(), 
        headers
    )

@app.get("/v1/orders/{order_id}")
async def get_order(order_id: str, token: str = Depends(get_current_user)):
    """Получение заказа по ID"""
    headers = {"Authorization": f"Bearer {token}"}
    return await proxy_request(ORDERS_SERVICE_URL, f"/v1/orders/{order_id}", "GET", headers=headers)

@app.get("/v1/orders")
async def get_orders_list(
    token: str = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(10, ge=1, le=100, description="Количество записей на странице"),
    status: Optional[str] = Query(None, description="Фильтр по статусу")
):
    """Список заказов пользователя"""
    params = f"?page={page}&limit={limit}"
    if status:
        params += f"&status={status}"
    
    headers = {"Authorization": f"Bearer {token}"}
    return await proxy_request(ORDERS_SERVICE_URL, f"/v1/orders{params}", "GET", headers=headers)

@app.patch("/v1/orders/{order_id}/status")
async def update_order_status(
    order_id: str, 
    status_data: OrderStatusUpdateRequest,
    token: str = Depends(get_current_user)
):
    """Обновление статуса заказа"""
    headers = {"Authorization": f"Bearer {token}"}
    return await proxy_request(
        ORDERS_SERVICE_URL, 
        f"/v1/orders/{order_id}/status", 
        "PATCH", 
        status_data.dict(), 
        headers
    )

@app.patch("/v1/orders/{order_id}/cancel")
async def cancel_order(order_id: str, token: str = Depends(get_current_user)):
    """Отмена заказа"""
    headers = {"Authorization": f"Bearer {token}"}
    return await proxy_request(ORDERS_SERVICE_URL, f"/v1/orders/{order_id}/cancel", "PATCH", headers=headers)

@app.get("/health")
async def health_check():
    """Health check gateway"""
    return {"status": "API Gateway is running"}

@app.get("/services/health")
async def services_health_check():
    """Health check всех сервисов"""
    services_status = {}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{USERS_SERVICE_URL}/health")
            services_status["users_service"] = response.status_code == 200
        except:
            services_status["users_service"] = False
        
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