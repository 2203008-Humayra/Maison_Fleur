import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to Python's import path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import database.cart as cart_module
from app import app
import app as app_module
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_homepage_loads_successfully(client):
    response = client.get("/")
    assert response.status_code == 200


def test_login_page_loads_successfully(client):
    response = client.get("/login")
    assert response.status_code == 200


def test_admin_login_page_loads_successfully(client):
    response = client.get("/admin-login")
    assert response.status_code == 200


def test_admin_dashboard_requires_login(client):
    response = client.get("/admin-dashboard")

    assert response.status_code == 302
    assert "/admin-login" in response.location


def test_customer_login_rejects_empty_credentials(client):
    response = client.post("/login", data={
        "email": "",
        "password": ""
    })

    assert response.status_code == 200
    assert b"Please enter your email and password." in response.data


def test_admin_login_rejects_empty_credentials(client):
    response = client.post("/admin-login", data={
        "email": "",
        "password": ""
    })

    assert response.status_code == 200
    assert b"Please enter your email and password." in response.data


def test_customer_login_rejects_invalid_credentials(client, monkeypatch):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None

    mock_connection = MagicMock()
    mock_connection.cursor.return_value = mock_cursor

    monkeypatch.setattr(
        app_module,
        "get_db_connection",
        lambda: mock_connection
    )

    response = client.post("/login", data={
        "email": "wrong@example.com",
        "password": "wrongpassword"
    })

    assert response.status_code == 200
    assert b"Invalid email or password." in response.data

    mock_connection.close.assert_called_once()
    mock_cursor.close.assert_called_once()


def test_customer_login_success(client, monkeypatch):
    mock_cursor = MagicMock()

    mock_cursor.fetchone.return_value = {
        "id": 1,
        "fullname": "Test User",
        "email": "test@example.com",
        "password_hash": generate_password_hash("correct123")
    }

    mock_connection = MagicMock()
    mock_connection.cursor.return_value = mock_cursor

    monkeypatch.setattr(
        app_module,
        "get_db_connection",
        lambda: mock_connection
    )

    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "correct123"
    })

    assert response.status_code == 302
    assert "/profile" in response.location

    with client.session_transaction() as session:
        assert session["user_id"] == 1
        assert session["user_name"] == "Test User"
        assert session["user_email"] == "test@example.com"

    mock_cursor.close.assert_called_once()
    mock_connection.close.assert_called_once()


def test_admin_login_success(client, monkeypatch):
    mock_cursor = MagicMock()

    mock_cursor.fetchone.return_value = {
        "id": 1,
        "fullname": "Test Admin",
        "email": "admin@example.com",
        "password_hash": generate_password_hash("admin123")
    }

    mock_connection = MagicMock()
    mock_connection.cursor.return_value = mock_cursor

    monkeypatch.setattr(
        app_module,
        "get_db_connection",
        lambda: mock_connection
    )

    response = client.post("/admin-login", data={
        "email": "admin@example.com",
        "password": "admin123"
    })

    assert response.status_code == 302
    assert "/admin-dashboard" in response.location

    with client.session_transaction() as session:
        assert session["admin_id"] == 1
        assert session["admin_name"] == "Test Admin"
        assert session["admin_email"] == "admin@example.com"

    mock_cursor.close.assert_called_once()
    mock_connection.close.assert_called_once()    


def test_admin_logout_clears_session(client):
    with client.session_transaction() as session:
        session["admin_id"] = 1
        session["admin_name"] = "Test Admin"

    response = client.get("/admin-logout")

    assert response.status_code == 302
    assert "/admin-login" in response.location

    with client.session_transaction() as session:
        assert "admin_id" not in session
        assert "admin_name" not in session



def test_admin_logout_without_session(client):
    response = client.get("/admin-logout")

    assert response.status_code == 302
    assert "/admin-login" in response.location


def test_catalog_loads_products_successfully(client, monkeypatch):
    mock_cursor = MagicMock()

    mock_cursor.fetchall.side_effect = [
        [
            {
                "id": 1,
                "name": "Red Rose",
                "image": "red_rose.jpg",
                "price": 150
            }
        ],
        [
            {
                "id": 32,
                "name": "Rosewood & Berry",
                "image": "rosewood.jpg",
                "price": 4500
            }
        ]
    ]

    mock_connection = MagicMock()
    mock_connection.cursor.return_value = mock_cursor

    monkeypatch.setattr(
        app_module,
        "get_db_connection",
        lambda: mock_connection
    )

    response = client.get("/catalog")

    assert response.status_code == 200
    assert b"Red Rose" in response.data
    

    mock_cursor.close.assert_called_once()
    mock_connection.close.assert_called_once()        


def test_basket_requires_customer_login(client):
    response = client.get("/basket")

    assert response.status_code == 302
    assert "/login" in response.location          


def test_checkout_requires_customer_login(client):
    response = client.get("/checkout")

    assert response.status_code == 302
    assert "/login" in response.location    


def test_cart_api_requires_customer_login(client):
    response = client.get("/api/cart")

    assert response.status_code == 401


def test_cart_api_rejects_invalid_data(client):
    with client.session_transaction() as session:
        session["user_id"] = 1

    response = client.post(
        "/api/cart",
        json={}
    )

    assert response.status_code == 400


def test_cart_api_rejects_negative_quantity(client):
    with client.session_transaction() as session:
        session["user_id"] = 1

    response = client.put(
        "/api/cart/1",
        json={"quantity": -1}
    )

    assert response.status_code == 400


def test_profile_requires_customer_login(client):
    response = client.get("/profile")

    assert response.status_code == 302
    assert "/login" in response.location 


def test_customer_logout_clears_session(client):
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Test Customer"
        session["user_email"] = "test@example.com"

    response = client.get("/logout")

    assert response.status_code == 302
    assert response.location.endswith("/")

    with client.session_transaction() as session:
        assert "user_id" not in session
        assert "user_name" not in session
        assert "user_email" not in session


def test_signup_page_loads_successfully(client):
    response = client.get("/signup")

    assert response.status_code == 200


def test_admin_add_product_requires_admin_login(client):
    response = client.post("/admin-add-product", data={})

    assert response.status_code == 302
    assert "/admin-login" in response.location


def test_admin_update_product_requires_admin_login(client):
    response = client.post(
        "/admin-update-product/1",
        data={}
    )

    assert response.status_code == 302
    assert "/admin-login" in response.location



def test_admin_toggle_product_requires_admin_login(client):
    response = client.post("/admin-toggle-product/1")

    assert response.status_code == 302
    assert "/admin-login" in response.location                    



def test_add_to_cart_success(monkeypatch):
    mock_cursor = MagicMock()
    mock_connection = MagicMock()

    mock_connection.cursor.return_value = mock_cursor

    monkeypatch.setattr(
        cart_module,
        "get_db_connection",
        lambda: mock_connection
    )

    product = {
        "name": "Red Rose",
        "image": "red_rose.jpg",
        "price": 150,
        "quantity": 2,
        "type": "flower"
    }

    result = cart_module.add_to_cart(1, product)

    assert result is True

    mock_cursor.execute.assert_called_once()
    mock_connection.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_connection.close.assert_called_once()  


def test_get_cart_items_success(monkeypatch):
    mock_cursor = MagicMock()
    mock_connection = MagicMock()

    expected_items = [
        {
            "id": 1,
            "product_name": "Red Rose",
            "product_image": "red_rose.jpg",
            "product_price": 150,
            "product_quantity": 2,
            "product_type": "flower"
        }
    ]

    mock_connection.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = expected_items

    monkeypatch.setattr(
        cart_module,
        "get_db_connection",
        lambda: mock_connection
    )

    result = cart_module.get_cart_items(1)

    assert result == expected_items

    mock_connection.cursor.assert_called_once_with(dictionary=True)
    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_connection.close.assert_called_once() 


def test_update_cart_quantity_success(monkeypatch):
    mock_cursor = MagicMock()
    mock_connection = MagicMock()

    mock_connection.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 1

    monkeypatch.setattr(
        cart_module,
        "get_db_connection",
        lambda: mock_connection
    )

    result = cart_module.update_cart_quantity(
        user_id=1,
        item_id=1,
        quantity=3
    )

    assert result is True

    mock_cursor.execute.assert_called_once()
    mock_connection.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_connection.close.assert_called_once()


def test_remove_from_cart_success(monkeypatch):
    mock_cursor = MagicMock()
    mock_connection = MagicMock()

    mock_connection.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 1

    monkeypatch.setattr(
        cart_module,
        "get_db_connection",
        lambda: mock_connection
    )

    result = cart_module.remove_from_cart(
        user_id=1,
        item_id=1
    )

    assert result is True

    mock_cursor.execute.assert_called_once()
    mock_connection.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_connection.close.assert_called_once()


def test_add_to_cart_connection_failure(monkeypatch):
    monkeypatch.setattr(
        cart_module,
        "get_db_connection",
        lambda: None
    )

    product = {
        "name": "Red Rose",
        "image": "red_rose.jpg",
        "price": 150,
        "quantity": 2,
        "type": "flower"
    }

    result = cart_module.add_to_cart(1, product)

    assert result is False


def test_get_cart_items_connection_failure(monkeypatch):
    monkeypatch.setattr(
        cart_module,
        "get_db_connection",
        lambda: None
    )

    result = cart_module.get_cart_items(1)

    assert result is None                                  