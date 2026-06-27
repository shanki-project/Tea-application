"""End-to-end RBAC + commerce flow against SQLite."""

from tests.conftest import auth_header


def _signup(client, name, email):
    r = client.post(
        "/api/auth/signup",
        json={"name": name, "email": email, "password": "password123"},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_signup_defaults_to_customer(client):
    h = _signup(client, "Cara", "cara@x.com")
    me = client.get("/api/auth/me", headers=h).json()
    assert me["role"] == "customer"
    assert me["is_active"] is True


def test_guest_can_browse_but_not_cart(client, super_admin):
    # public listing works without auth
    assert client.get("/api/products").status_code == 200
    # cart requires auth
    assert client.get("/api/cart").status_code == 401


def test_customer_cannot_create_product(client):
    h = _signup(client, "Cara", "cara@x.com")
    r = client.post("/api/products", json={"name": "X", "price": 10}, headers=h)
    assert r.status_code == 403


def test_full_commerce_flow(client, super_admin):
    admin_h = auth_header(client, "root@shankistea.com", "password123")

    # Super Admin creates a product
    r = client.post(
        "/api/products",
        json={"name": "Dawn", "price": 890, "stock_qty": 5, "category": "Green tea",
              "ingredients": "Tulsi. Rose."},
        headers=admin_h,
    )
    assert r.status_code == 201, r.text
    product = r.json()
    assert product["slug"] == "dawn"
    assert product["is_low_stock"] is True  # 5 <= 10

    # Customer signs up, adds to cart, checks out
    cust_h = _signup(client, "Cara", "cara@x.com")
    r = client.post(
        "/api/cart/items",
        json={"product_id": product["id"], "quantity": 2},
        headers=cust_h,
    )
    assert r.status_code == 201
    assert r.json()["item_count"] == 2

    r = client.post(
        "/api/orders/checkout",
        json={"shipping_address": "12 Tea Lane, Assam", "payment_method": "card"},
        headers=cust_h,
    )
    assert r.status_code == 201, r.text
    result = r.json()
    assert result["payment_status"] == "successful"
    assert result["fake_transaction_id"].startswith("TXN-")
    order_id = result["order"]["id"]

    # Stock auto-decremented 5 -> 3
    p = client.get("/api/products/dawn").json()
    assert p["stock_qty"] == 3

    # Cart cleared
    assert client.get("/api/cart", headers=cust_h).json()["item_count"] == 0

    # Customer sees order in history
    orders = client.get("/api/orders", headers=cust_h).json()
    assert len(orders) == 1 and orders[0]["status"] == "placed"

    # Admin advances status placed -> packed (valid), but placed -> delivered (invalid)
    bad = client.patch(
        f"/api/orders/{order_id}/status", json={"status": "delivered"}, headers=admin_h
    )
    assert bad.status_code == 400
    ok = client.patch(
        f"/api/orders/{order_id}/status", json={"status": "packed"}, headers=admin_h
    )
    assert ok.status_code == 200 and ok.json()["status"] == "packed"

    # Customer can review a purchased product
    r = client.post(
        f"/api/products/{product['id']}/reviews",
        json={"rating": 5, "comment": "Sublime."},
        headers=cust_h,
    )
    assert r.status_code == 201, r.text
    reviews = client.get(f"/api/products/{product['id']}/reviews").json()
    assert reviews[0]["rating"] == 5 and reviews[0]["user_name"] == "Cara"


def test_review_requires_purchase(client, super_admin):
    admin_h = auth_header(client, "root@shankistea.com", "password123")
    pid = client.post(
        "/api/products", json={"name": "Night", "price": 1050, "stock_qty": 3},
        headers=admin_h,
    ).json()["id"]
    cust_h = _signup(client, "Cara", "cara@x.com")
    r = client.post(
        f"/api/products/{pid}/reviews", json={"rating": 4}, headers=cust_h
    )
    assert r.status_code == 403  # never purchased


def test_order_cancel_restocks(client, super_admin):
    admin_h = auth_header(client, "root@shankistea.com", "password123")
    prod = client.post(
        "/api/products", json={"name": "Dawn", "price": 890, "stock_qty": 10},
        headers=admin_h,
    ).json()
    cust_h = _signup(client, "Cara", "cara@x.com")
    client.post("/api/cart/items", json={"product_id": prod["id"], "quantity": 4}, headers=cust_h)
    order = client.post(
        "/api/orders/checkout",
        json={"shipping_address": "12 Tea Lane", "payment_method": "card"},
        headers=cust_h,
    ).json()["order"]
    assert client.get("/api/products/dawn").json()["stock_qty"] == 6  # 10-4

    # customer cancels -> restocked back to 10
    r = client.post(f"/api/orders/{order['id']}/cancel", headers=cust_h)
    assert r.status_code == 200 and r.json()["status"] == "cancelled"
    assert client.get("/api/products/dawn").json()["stock_qty"] == 10


def test_change_password(client):
    h = _signup(client, "Cara", "cara@x.com")
    bad = client.post(
        "/api/auth/change-password",
        json={"current_password": "wrong", "new_password": "newpassword123"},
        headers=h,
    )
    assert bad.status_code == 400
    ok = client.post(
        "/api/auth/change-password",
        json={"current_password": "password123", "new_password": "newpassword123"},
        headers=h,
    )
    assert ok.status_code == 200
    assert auth_header(client, "cara@x.com", "newpassword123")  # new password works


def test_my_reviews_edit_delete(client, super_admin):
    admin_h = auth_header(client, "root@shankistea.com", "password123")
    pid = client.post(
        "/api/products", json={"name": "Dusk", "price": 950, "stock_qty": 5},
        headers=admin_h,
    ).json()["id"]
    cust_h = _signup(client, "Cara", "cara@x.com")
    client.post("/api/cart/items", json={"product_id": pid, "quantity": 1}, headers=cust_h)
    client.post(
        "/api/orders/checkout",
        json={"shipping_address": "12 Tea Lane", "payment_method": "card"},
        headers=cust_h,
    )
    rev = client.post(
        f"/api/products/{pid}/reviews", json={"rating": 4, "comment": "good"}, headers=cust_h
    ).json()
    mine = client.get("/api/reviews/mine", headers=cust_h).json()
    assert len(mine) == 1 and mine[0]["product_name"] == "Dusk"
    # edit
    up = client.put(f"/api/reviews/{rev['id']}", json={"rating": 2}, headers=cust_h)
    assert up.status_code == 200 and up.json()["rating"] == 2
    # delete
    assert client.delete(f"/api/reviews/{rev['id']}", headers=cust_h).status_code == 204
    assert client.get("/api/reviews/mine", headers=cust_h).json() == []


def test_admin_sees_customer_and_analytics(client, super_admin):
    admin_h = auth_header(client, "root@shankistea.com", "password123")
    pid = client.post(
        "/api/products", json={"name": "Night", "price": 1050, "stock_qty": 9},
        headers=admin_h,
    ).json()["id"]
    cust_h = _signup(client, "Cara Mia", "cara@x.com")
    client.post("/api/cart/items", json={"product_id": pid, "quantity": 2}, headers=cust_h)
    client.post(
        "/api/orders/checkout",
        json={"shipping_address": "12 Tea Lane", "payment_method": "card"},
        headers=cust_h,
    )
    orders = client.get("/api/dashboard/orders", headers=admin_h).json()
    assert orders[0]["customer_name"] == "Cara Mia"
    assert orders[0]["customer_email"] == "cara@x.com"

    a = client.get("/api/dashboard/analytics", headers=admin_h).json()
    assert a["revenue"] == 2100.0
    assert a["top_products"][0]["name"] == "Night"
    assert a["top_products"][0]["qty"] == 2


def test_super_admin_manages_accounts_and_audit(client, super_admin):
    admin_h = auth_header(client, "root@shankistea.com", "password123")

    # create an Admin/Staff account
    r = client.post(
        "/api/users/admins",
        json={"name": "Stan", "email": "stan@x.com", "password": "password123",
              "role": "admin"},
        headers=admin_h,
    )
    assert r.status_code == 201
    staff_h = auth_header(client, "stan@x.com", "password123")

    # staff can manage products but NOT view users or audit logs
    assert client.post(
        "/api/products", json={"name": "Dusk", "price": 950, "stock_qty": 20},
        headers=staff_h,
    ).status_code == 201
    assert client.get("/api/users", headers=staff_h).status_code == 403
    assert client.get("/api/dashboard/audit-logs", headers=staff_h).status_code == 403

    # super admin sees audit logs (product creates were logged)
    logs = client.get("/api/dashboard/audit-logs", headers=admin_h).json()
    assert any(log["action"] == "create_product" for log in logs)

    # super admin cannot delete self
    assert client.delete(
        f"/api/users/{super_admin.id}", headers=admin_h
    ).status_code == 400
