import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_endpoint():
    """Тест health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "API Gateway is running"}

def test_services_health():
    """Тест проверки здоровья всех сервисов"""
    response = client.get("/services/health")
    assert response.status_code == 200
    data = response.json()
    assert data["gateway"] == True
    assert "services" in data
    assert "users_service" in data["services"]
    assert "orders_service" in data["services"]

def test_root_endpoint():
    """Тест корневого endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Construction Control System API Gateway" in data["message"]
    assert "version" in data