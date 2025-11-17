import pytest
import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

class TestUserWorkflow:
    """Тесты полного workflow пользователя"""
    
    def test_register_and_login(self):
        # Регистрация нового пользователя
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": email,
            "name": "Test User",
            "password": "testpass123",
            "roles": ["engineer"]
        }
        response = client.post("/v1/register", json=user_data)
        assert response.status_code == 201
        user_id = response.json()["id"]
        assert user_id is not None
        
        # Логин с правильными данными
        login_data = {
            "email": email,
            "password": "testpass123"
        }
        response = client.post("/v1/login", json=login_data)
        assert response.status_code == 200
        token = response.json()["access_token"]
        assert token is not None
        
        return token

class TestEngineerWorkflow:
    """Тесты для инженера"""
    
    def test_engineer_full_workflow(self):
        # Регистрируем и логиним инженера
        email = f"engineer_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": email,
            "name": "Engineer User",
            "password": "engineerpass123",
            "roles": ["engineer"]
        }
        client.post("/v1/register", json=user_data)
        
        login_data = {"email": email, "password": "engineerpass123"}
        login_response = client.post("/v1/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Получаем профиль
        response = client.get("/v1/profile", headers=headers)
        assert response.status_code == 200
        assert response.json()["email"] == email
        
        # 2. Создаем заказ
        order_data = {
            "items": [
                {
                    "product": "Construction Material",
                    "quantity": 10,
                    "price": 150.50
                },
                {
                    "product": "Tools",
                    "quantity": 2,
                    "price": 300.00
                }
            ]
        }
        response = client.post("/v1/orders", json=order_data, headers=headers)
        assert response.status_code == 201
        order = response.json()
        order_id = order["id"]
        assert order["status"] == "created"
        assert order["total_amount"] == 10*150.50 + 2*300.00
        
        # 3. Получаем заказ по ID
        response = client.get(f"/v1/orders/{order_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == order_id
        
        # 4. Получаем список заказов
        response = client.get("/v1/orders", headers=headers)
        assert response.status_code == 200
        orders_data = response.json()
        assert orders_data["total"] >= 1
        assert len(orders_data["orders"]) >= 1
        
        # 5. Отменяем заказ (инженер может отменить свой заказ в статусе created)
        response = client.patch(f"/v1/orders/{order_id}/cancel", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
        
        return token, order_id

class TestManagerWorkflow:
    """Тесты для менеджера"""
    
    def test_manager_full_workflow(self):
        # Регистрируем менеджера
        email = f"manager_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": email,
            "name": "Manager User",
            "password": "managerpass123",
            "roles": ["manager"]
        }
        client.post("/v1/register", json=user_data)
        
        login_data = {"email": email, "password": "managerpass123"}
        login_response = client.post("/v1/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Менеджер может создать заказ
        order_data = {
            "items": [
                {
                    "product": "Manager Order Item",
                    "quantity": 5,
                    "price": 200.00
                }
            ]
        }
        response = client.post("/v1/orders", json=order_data, headers=headers)
        assert response.status_code == 201
        order_id = response.json()["id"]
        
        # 2. Менеджер может изменить статус своего заказа
        status_data = {"status": "in_progress"}
        response = client.patch(f"/v1/orders/{order_id}/status", json=status_data, headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"
        
        # 3. Менеджер видит все заказы (не только свои)
        response = client.get("/v1/orders", headers=headers)
        assert response.status_code == 200
        # Должен быть хотя бы 1 заказ (может быть больше из других тестов)
        assert response.json()["total"] >= 1
        
        return token

class TestAdminWorkflow:
    """Тесты для администратора"""
    
    def test_admin_full_workflow(self):
        # Регистрируем админа
        email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": email,
            "name": "Admin User",
            "password": "adminpass123",
            "roles": ["admin"]
        }
        client.post("/v1/register", json=user_data)
        
        login_data = {"email": email, "password": "adminpass123"}
        login_response = client.post("/v1/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Админ может получить список пользователей
        response = client.get("/v1/admin/users", headers=headers)
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 1  # Должен быть хотя бы сам админ
        
        # 2. Админ может создать нового пользователя
        new_user_data = {
            "email": f"newuser_{uuid.uuid4().hex[:8]}@example.com",
            "name": "New User Created by Admin",
            "password": "newuserpass123",
            "roles": ["engineer", "manager"]
        }
        response = client.post("/v1/admin/users", json=new_user_data, headers=headers)
        assert response.status_code == 201
        assert response.json()["email"] == new_user_data["email"]
        
        return token

class TestSecurity:
    """Тесты безопасности и прав доступа"""
    
    def test_access_without_token(self):
        """Доступ без токена должен быть запрещен"""
        response = client.get("/v1/profile")
        assert response.status_code == 401
        
        response = client.get("/v1/orders")
        assert response.status_code == 401
        
        response = client.post("/v1/orders", json={"items": []})
        assert response.status_code == 401
    
    def test_engineer_cannot_access_admin_endpoints(self):
        """Инженер не может получить доступ к админским endpoint"""
        # Создаем инженера
        email = f"engineer_sec_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": email,
            "name": "Security Engineer",
            "password": "pass123",
            "roles": ["engineer"]
        }
        client.post("/v1/register", json=user_data)
        
        login_data = {"email": email, "password": "pass123"}
        login_response = client.post("/v1/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Инженер не может получить список пользователей
        response = client.get("/v1/admin/users", headers=headers)
        assert response.status_code == 403
        
        # Инженер не может создавать пользователей
        new_user_data = {
            "email": "test@example.com",
            "name": "Test",
            "password": "pass",
            "roles": ["engineer"]
        }
        response = client.post("/v1/admin/users", json=new_user_data, headers=headers)
        assert response.status_code == 403
    
    def test_engineer_cannot_change_order_status(self):
        """Инженер не может менять статус заказов"""
        # Создаем инженера и его заказ
        email = f"engineer_status_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": email,
            "name": "Status Engineer",
            "password": "pass123",
            "roles": ["engineer"]
        }
        client.post("/v1/register", json=user_data)
        
        login_data = {"email": email, "password": "pass123"}
        login_response = client.post("/v1/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Создаем заказ
        order_data = {
            "items": [{"product": "test", "quantity": 1, "price": 100.0}]
        }
        response = client.post("/v1/orders", json=order_data, headers=headers)
        order_id = response.json()["id"]
        
        # Инженер не может изменить статус
        status_data = {"status": "in_progress"}
        response = client.patch(f"/v1/orders/{order_id}/status", json=status_data, headers=headers)
        assert response.status_code == 403

class TestErrorScenarios:
    """Тесты обработки ошибок"""
    
    def test_register_duplicate_email(self):
        """Регистрация с существующим email должна вернуть ошибку"""
        email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": email,
            "name": "First User",
            "password": "pass123",
            "roles": ["engineer"]
        }
        # Первая регистрация - успешно
        response = client.post("/v1/register", json=user_data)
        assert response.status_code == 201
        
        # Вторая регистрация - ошибка
        response = client.post("/v1/register", json=user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_login_wrong_password(self):
        """Логин с неправильным паролем"""
        email = f"wrongpass_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": email,
            "name": "Wrong Pass User",
            "password": "correctpass",
            "roles": ["engineer"]
        }
        client.post("/v1/register", json=user_data)
        
        login_data = {"email": email, "password": "wrongpassword"}
        response = client.post("/v1/login", json=login_data)
        assert response.status_code == 401
    
    def test_invalid_order_data(self):
        """Создание заказа с невалидными данными"""
        # Создаем пользователя для теста
        email = f"invalid_order_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": email,
            "name": "Invalid Order User",
            "password": "pass123",
            "roles": ["engineer"]
        }
        client.post("/v1/register", json=user_data)
        
        login_data = {"email": email, "password": "pass123"}
        login_response = client.post("/v1/login", json=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Невалидные данные - отрицательное количество
        invalid_order = {
            "items": [
                {
                    "product": "test",
                    "quantity": -1,  # Отрицательное количество
                    "price": 100.0
                }
            ]
        }
        response = client.post("/v1/orders", json=invalid_order, headers=headers)
        assert response.status_code == 422  # Unprocessable Entity