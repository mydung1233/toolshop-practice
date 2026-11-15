"""Buoi 2 - API testing with APIRequestContext (not the requests library).

Fixtures you can use (see conftest.py): api, test_user, auth_token, auth_headers
Helpers: register_user(api, email, password), new_email(), strong_password()

Run:  pytest tests/buoi2/test_b2_api.py -v
"""
import json
from pathlib import Path

import pytest

from conftest import new_email, register_user, strong_password  # noqa: F401  (you will need them)

KEYWORDS = json.loads((Path(__file__).parents[2] / "data" / "search_keywords.json").read_text())


# ---------------------------------------------------------------- B2.1 (together)
@pytest.mark.smoke
@pytest.mark.api
def test_b2_1_status_returns_toolshop(api):
    """Goal: API is alive. Precondition: none. Expected: 200 and app_name Toolshop."""
    response = api.get("/status")
    assert response.status == 200, response.text()
    assert response.json()["app_name"] == "Toolshop"


# ---------------------------------------------------------------- B2.2
def test_b2_2_products_first_page_has_pagination_and_product_shape(api):
    """Goal: contract of GET /products.
    Precondition: none.
    Expected: keys current_page/data/per_page/total/last_page, 0 < len(data) <= per_page,
    every product has id (str or int), a non-empty name and a price > 0.
    Rule: NO absolute numbers (PROD has 50 products, BUGGY 26)."""
    response = api.get("/products")

    assert response.status == 200, response.text()

    body = response.json()

    required_keys = [
        "current_page",
        "data",
        "per_page",
        "total",
        "last_page",
    ]

    for key in required_keys:
        assert key in body

    products = body["data"]

    assert isinstance(products, list)
    assert 0 < len(products) <= body["per_page"]

    for product in products:
        assert isinstance(product["id"], (str, int))
        assert isinstance(product["name"], str)
        assert product["name"].strip() != ""
        assert product["price"] > 0


# ---------------------------------------------------------------- B2.3 data-driven
@pytest.mark.parametrize("case", KEYWORDS, ids=[c["keyword"] for c in KEYWORDS])
def test_b2_3_search_api_returns_only_matching_names(api, case):
    """Goal: GET /products/search?q=... filters by name.
    Precondition: none.
    Expected: at least one result and every name contains the keyword.
    Extra: add "saw" and "wrench" to data/search_keywords.json - no code change needed."""
    keyword = case["keyword"]
    expected = case["must_contain"]

    response = api.get("/products/search", params={"q": keyword})

    assert response.status == 200, response.text()

    body = response.json()
    products = body["data"]

    assert len(products) > 0

    for product in products:
        assert expected.lower() in product["name"].lower()


# ---------------------------------------------------------------- B2.4 errors
# TODO B2.4a: one parametrized test: GET /users/me -> 401, GET /products/does-not-exist -> 404

@pytest.mark.parametrize(
    "endpoint, expected_status",
    [
        ("/users/me", 401),
        ("/products/does-not-exist", 404),
    ],
)
def test_b2_4a_protected_or_missing_resource_returns_4xx(
    api, endpoint, expected_status
):
    response = api.get(endpoint)

    assert response.status == expected_status, response.text()
       


def test_b2_4b_register_empty_body_returns_422_with_field_errors(api):
    """Goal: server-side validation. Precondition: none.
    Expected: 422 and error lists for 'email' and 'password'."""
    response = api.post("/users/register", data={})

    assert response.status == 422, response.text()

    body = response.json()

    assert "email" in body
    assert "password" in body

    assert isinstance(body["email"], list)
    assert isinstance(body["password"], list)


def test_b2_4c_register_leaked_password_is_rejected(api):
    """Goal: password policy. Precondition: none.
    Expected: 422 because 'Welcome01!' appears in known data leaks."""
    
    response = api.post(
        "/users/register",
        data={
            "first_name": "Test",
            "last_name": "User",
            "address": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "country": "VN",
            "postcode": "550000",
            "phone": "0123456789",
            "dob": "2000-01-01",
            "email": new_email(),
            "password": "Welcome01!",
        },
    )

    assert response.status == 422, response.text()



# ---------------------------------------------------------------- B2.5 token
def test_b2_5a_users_me_with_token_returns_own_profile(api, auth_headers, test_user):
    """Goal: bearer token grants access. Precondition: user registered by the fixture.
    Expected: 200 and the same email."""
   
    response = api.get("/users/me", headers=auth_headers)

    assert response.status == 200, response.text()

    body = response.json()

    assert body["email"] == test_user["email"]



def test_b2_5b_register_response_does_not_expose_password(api):
    """Goal: no secrets in responses. Precondition: none.
    Expected: 201 and no 'password' key in the JSON body."""
    
    email = new_email()
    password = strong_password()

    response = register_user(api, email, password)

    assert response.status == 201, response.text()

    body = response.json()

    assert "password" not in body



# ---------------------------------------------------------------- B2.6 your own fixture
# TODO B2.6: write a fixture `new_cart` (in this file) that POSTs /carts and returns the id.

@pytest.fixture
def new_cart(api):
    response = api.post("/carts")

    assert response.status == 201, response.text()

    return response.json()["id"]

def test_b2_6_cart_add_product_quantity_two_is_stored(api, new_cart):
    """Goal: cart API stores the quantity.
    Precondition: a new cart (your fixture) and the first product of GET /products.
    Expected: GET /carts/{id} has exactly 1 item, quantity 2, same product_id."""
   
    # Lay san pham dau tien
    response = api.get("/products")
    assert response.status == 200, response.text()

    products = response.json()["data"]
    assert len(products) > 0

    product_id = products[0]["id"]

    # Them san pham vao gio voi so luong 2
    add_response = api.post(
        f"/carts/{new_cart}",
        data={
            "product_id": product_id,
            "quantity": 2
        }
    )

    assert add_response.status in (200, 201), add_response.text()

    # Kiem tra gio hang
    cart_response = api.get(f"/carts/{new_cart}")

    assert cart_response.status == 200, cart_response.text()

    cart = cart_response.json()
    items = cart["cart_items"]

    assert len(items) == 1
    assert items[0]["quantity"] == 2
    assert items[0]["product_id"] == product_id

