import pytest
import requests

API_URL = "https://dummyjson.com"

# Согласно документации DummyJSON, это валидные тестовые данные
TEST_USERNAME = "emilys"
TEST_PASSWORD = "emilyspass"

@pytest.fixture(scope="module")
def auth_data():
    """Фикстура для получения токена и ID пользователя перед запуском тестов корзины."""
    request_body = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    resp = requests.post(f"{API_URL}/auth/login", json=request_body)
    res_json = resp.json()
    
    return {
        "token": res_json.get("accessToken", res_json.get("token")),
        "userId": res_json.get("id")
    }

# --- 1 и 2. Авторизация пользователя ---

def test_login_success():
    """1. Успешная авторизация (POST /auth/login)"""
    request_body = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
    resp = requests.post(f"{API_URL}/auth/login", json=request_body)
    
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    res_json = resp.json()
    assert "token" in res_json or "accessToken" in res_json, "Token is missing in response"
    assert res_json.get("username") == TEST_USERNAME

def test_login_invalid_password():
    """2. Неуспешная авторизация с неверным паролем (POST /auth/login)"""
    request_body = {"username": TEST_USERNAME, "password": "wrong_password!"}
    resp = requests.post(f"{API_URL}/auth/login", json=request_body)
    
    assert resp.status_code == 400, "Expected 400 Bad Request for invalid credentials"
    assert "message" in resp.json()

# --- 3 и 4. Получение данных авторизованного пользователя ---

def test_get_current_user_with_token(auth_data):
    """3. Получение текущего пользователя с токеном (GET /auth/me)"""
    headers = {"Authorization": f"Bearer {auth_data['token']}"}
    resp = requests.get(f"{API_URL}/auth/me", headers=headers)
    
    assert resp.status_code == 200
    assert resp.json().get("id") == auth_data["userId"]

def test_get_current_user_without_token():
    """4. Получение текущего пользователя без токена (GET /auth/me)"""
    resp = requests.get(f"{API_URL}/auth/me")
    
    # API возвращает 401 Unauthorized, если токен не передан
    assert resp.status_code == 401
    res_json = resp.json()
    assert res_json.get("name") == "TokenExpiredError" or "message" in res_json

# --- 5 - 10. Работа с корзиной ---

def test_get_user_carts(auth_data):
    """5. Получение корзин пользователя (GET /carts/user/{userId})"""
    user_id = auth_data["userId"]
    resp = requests.get(f"{API_URL}/carts/user/{user_id}")
    
    assert resp.status_code == 200
    res_json = resp.json()
    assert "carts" in res_json
    assert isinstance(res_json["carts"], list)

def test_get_cart_by_id():
    """6. Получение корзины по id (GET /carts/{cartId})"""
    target_cart_id = 1
    resp = requests.get(f"{API_URL}/carts/{target_cart_id}")
    
    assert resp.status_code == 200
    assert resp.json().get("id") == target_cart_id

def test_add_cart(auth_data):
    """7. Создание корзины (POST /carts/add)"""
    request_body = {
        "userId": auth_data["userId"],
        "products": [
            {"id": 1, "quantity": 2}
        ]
    }
    resp = requests.post(f"{API_URL}/carts/add", json=request_body)
    
    assert resp.status_code in (200, 201), "Expected 200 or 201 Created"
    res_json = resp.json()
    assert res_json.get("userId") == auth_data["userId"]
    assert len(res_json.get("products", [])) > 0

def test_update_cart():
    """8. Обновление корзины (PUT /carts/{cartId})"""
    target_cart_id = 1
    request_body = {
        "merge": True,
        "products": [
            {"id": 1, "quantity": 5}
        ]
    }
    resp = requests.put(f"{API_URL}/carts/{target_cart_id}", json=request_body)
    
    assert resp.status_code == 200
    # Проверяем, что ответ возвращает обновляемую корзину
    assert resp.json().get("id") == target_cart_id

def test_delete_cart():
    """9. Удаление корзины (DELETE /carts/{cartId})"""
    target_cart_id = 1
    resp = requests.delete(f"{API_URL}/carts/{target_cart_id}")
    
    assert resp.status_code == 200
    # DummyJSON API при удалении возвращает флаг isDeleted
    assert resp.json().get("isDeleted") is True

def test_get_cart_not_found():
    """10. Негативная проверка для корзины - несуществующий cartId"""
    non_existent_cart_id = 9999999
    resp = requests.get(f"{API_URL}/carts/{non_existent_cart_id}")
    
    # Ожидаем 404 Not Found, так как корзины не существует
    assert resp.status_code == 404
    assert "message" in resp.json()