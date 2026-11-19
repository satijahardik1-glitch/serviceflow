from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core.config import Settings
from app.core.crypto import decrypt
from app.db.session import engine


def future(days=3, hour=10):
    d = datetime.now(timezone.utc) + timedelta(days=days)
    return d.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()


def tech_id(client, email_name="Rajesh Kumar"):
    return next(t for t in client.get("/api/technicians/match").json() if t["name"] == email_name)["id"]


def booking_body(client, when=None, name="Rajesh Kumar", **kw):
    body = dict(technician_id=tech_id(client, name), category_id=1, problem_description="Sparking socket in the kitchen",
                address="14 Model Town", city="Jalandhar", scheduled_at=when or future())
    body.update(kw)
    return body


# ------------------------------------------------------------------ auth & RBAC
def test_login_success_and_wrong_password(client):
    assert client.post("/api/auth/login", json={"email": "neha@example.com", "password": "Customer@123"}).status_code == 200
    assert client.post("/api/auth/login", json={"email": "neha@example.com", "password": "nope"}).status_code == 401


def test_protected_routes_require_auth_and_role(client, customer):
    assert client.get("/api/admin/metrics").status_code == 401
    assert client.get("/api/admin/metrics", headers=customer).status_code == 403
    assert client.get("/api/technicians/me", headers=customer).status_code == 403
    assert client.get("/api/bookings/mine", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_register_rules(client):
    ok = {"name": "Test User", "email": "t@x.com", "password": "password1"}
    assert client.post("/api/auth/register", json=ok).status_code == 201
    assert client.post("/api/auth/register", json=ok).status_code == 409                       # duplicate email
    assert client.post("/api/auth/register", json={**ok, "email": "a@x.com", "role": "admin"}).status_code == 422  # no self-service admin
    assert client.post("/api/auth/register", json={**ok, "email": "b@x.com", "password": "alllettersonly"}).status_code == 422
    tech = {**ok, "email": "c@x.com", "role": "technician"}
    assert client.post("/api/auth/register", json=tech).status_code == 422                     # needs city + categories
    r = client.post("/api/auth/register", json={**tech, "city": "Patiala", "category_ids": [2]})
    assert r.status_code == 201 and r.json()["user"]["role"] == "technician"
    assert client.post("/api/auth/register", json={**tech, "email": "d@x.com", "city": "P", "category_ids": [999]}).status_code == 422


def test_login_lockout_after_repeated_failures(client):
    for _ in range(5):
        assert client.post("/api/auth/login", json={"email": "neha@example.com", "password": "bad"}).status_code == 401
    r = client.post("/api/auth/login", json={"email": "neha@example.com", "password": "Customer@123"})
    assert r.status_code == 429 and "Retry-After" in r.headers


# ------------------------------------------------------------------ diagnosis & matching
def test_diagnosis_rules(client):
    r = client.post("/api/services/diagnose", json={"category_id": 1, "description": "lights flicker and there is a burning smell"}).json()
    assert "safety-critical" in r["diagnosis"] and not r["is_fallback"]
    r = client.post("/api/services/diagnose", json={"category_id": 3, "symptoms": ["Not cooling"]}).json()
    assert r["min_price"] < r["max_price"] and r["confidence"] > 0.5
    assert client.post("/api/services/diagnose", json={"category_id": 2, "description": "something odd"}).json()["is_fallback"]
    assert client.post("/api/services/diagnose", json={"category_id": 1}).status_code == 422
    assert client.post("/api/services/diagnose", json={"category_id": 999, "description": "x"}).status_code == 404


def test_matching_only_verified_and_ranked(client):
    everyone = client.get("/api/technicians/match").json()
    assert all(t["verification_status"] == "verified" for t in everyone)
    assert "Sandeep Verma" not in [t["name"] for t in everyone]  # pending
    assert "Vikram Chauhan" not in [t["name"] for t in everyone]  # rejected
    ranked = client.get("/api/technicians/match", params={"category_id": 1, "city": "Jalandhar"}).json()
    assert ranked[0]["name"] == "Rajesh Kumar" and ranked[0]["score"] >= ranked[-1]["score"]
    assert all(any(c["id"] == 1 for c in t["categories"]) for t in ranked)
    assert client.get("/api/technicians/match", params={"available_only": True}).json()


def test_unverified_profile_hidden_from_public(client, admin):
    pending = client.get("/api/admin/technicians", params={"status": "pending"}, headers=admin).json()[0]
    assert client.get(f"/api/technicians/{pending['id']}").status_code == 404
    assert client.get(f"/api/technicians/{pending['id']}", headers=admin).status_code == 200


# ------------------------------------------------------------------ booking lifecycle
def test_full_booking_lifecycle_and_review(client, customer, rajesh):
    before = client.get(f"/api/technicians/{tech_id(client)}").json()
    r = client.post("/api/bookings", json=booking_body(client), headers=customer)
    assert r.status_code == 201, r.text
    b = r.json()
    assert b["status"] == "pending" and b["estimated_min_price"] > 0 and "safety-critical" in b["diagnosis"]
    assert b["customer_phone"] is None  # hidden until accepted

    assert client.patch(f"/api/bookings/{b['id']}/status", json={"status": "completed"}, headers=rajesh).status_code == 409
    assert client.post(f"/api/bookings/{b['id']}/review", json={"rating": 5}, headers=customer).status_code == 409  # not completed
    for s in ("accepted", "in_progress", "completed"):
        r = client.patch(f"/api/bookings/{b['id']}/status", json={"status": s}, headers=rajesh)
        assert r.status_code == 200 and r.json()["status"] == s
    assert r.json()["customer_phone"]  # visible once accepted

    assert client.post(f"/api/bookings/{b['id']}/review", json={"rating": 6}, headers=customer).status_code == 422
    assert client.post(f"/api/bookings/{b['id']}/review", json={"rating": 1, "comment": "late"}, headers=customer).status_code == 201
    assert client.post(f"/api/bookings/{b['id']}/review", json={"rating": 1}, headers=customer).status_code == 409  # once only
    after = client.get(f"/api/technicians/{before['id']}").json()
    assert after["review_count"] == before["review_count"] + 1 and after["avg_rating"] < before["avg_rating"]


def test_booking_access_control(client, customer, customer2, rajesh, login):
    b = client.post("/api/bookings", json=booking_body(client), headers=customer).json()
    assert client.get(f"/api/bookings/{b['id']}", headers=customer2).status_code == 403
    assert client.get(f"/api/bookings/{b['id']}", headers=login("amandeep@serviceflow.com")).status_code == 403
    assert client.get(f"/api/bookings/{b['id']}", headers=rajesh).status_code == 200
    assert client.patch(f"/api/bookings/{b['id']}/status", json={"status": "cancelled"}, headers=customer2).status_code == 403
    assert client.patch(f"/api/bookings/{b['id']}/status", json={"status": "accepted"}, headers=customer).status_code == 409  # customers can't accept
    assert client.patch(f"/api/bookings/{b['id']}/status", json={"status": "cancelled"}, headers=customer).json()["status"] == "cancelled"


def test_booking_validation(client, customer, rajesh):
    soon = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    assert client.post("/api/bookings", json=booking_body(client, when=soon), headers=customer).status_code == 422
    assert client.post("/api/bookings", json=booking_body(client, category_id=2), headers=customer).status_code == 400  # skill mismatch
    assert client.post("/api/bookings", json=booking_body(client, technician_id=9999), headers=customer).status_code == 404
    assert client.post("/api/bookings", json=booking_body(client), headers=rajesh).status_code == 403  # only customers book
    client.patch("/api/technicians/me/availability", json={"is_available": False}, headers=rajesh)
    assert client.post("/api/bookings", json=booking_body(client), headers=customer).status_code == 409


def test_double_booking_prevented(client, customer, customer2, rajesh):
    first = client.post("/api/bookings", json=booking_body(client, when=future(4, 10)), headers=customer).json()
    clash = client.post("/api/bookings", json=booking_body(client, when=future(4, 10)), headers=customer2).json()  # both pending: allowed
    assert client.patch(f"/api/bookings/{first['id']}/status", json={"status": "accepted"}, headers=rajesh).status_code == 200
    # accepting the overlapping one must now fail (the race the pending-only check could miss)
    assert client.patch(f"/api/bookings/{clash['id']}/status", json={"status": "accepted"}, headers=rajesh).status_code == 409
    # and new requests for that slot are refused outright
    assert client.post("/api/bookings", json=booking_body(client, when=future(4, 11)), headers=customer2).status_code == 409
    assert client.post("/api/bookings", json=booking_body(client, when=future(4, 14)), headers=customer2).status_code == 201


def test_saved_technicians(client, customer, rajesh):
    tid = tech_id(client, "Amandeep Singh")
    assert client.post(f"/api/technicians/{tid}/save", headers=customer).status_code == 201
    assert client.post(f"/api/technicians/{tid}/save", headers=customer).status_code == 201  # idempotent
    assert tid in [t["id"] for t in client.get("/api/technicians/saved", headers=customer).json()]
    assert client.get(f"/api/technicians/{tid}", headers=customer).json()["is_saved"] is True
    assert client.post(f"/api/technicians/{tid}/save", headers=rajesh).status_code == 403
    client.delete(f"/api/technicians/{tid}/save", headers=customer)
    assert tid not in [t["id"] for t in client.get("/api/technicians/saved", headers=customer).json()]


# ------------------------------------------------------------------ ID encryption & verification
def test_id_number_encrypted_at_rest_and_masked(client, rajesh, admin):
    with engine.connect() as c:
        raw = c.execute(text("SELECT id_document_number FROM technician_profiles WHERE id_document_number IS NOT NULL")).scalars().all()
    assert raw and all(v.startswith("gAAAA") for v in raw)  # ciphertext only
    me = client.get("/api/technicians/me", headers=rajesh).json()
    assert me["id_document_number"].startswith("••••") and me["id_document_number"].endswith("1201")
    full = {t["name"]: t for t in client.get("/api/admin/technicians", headers=admin).json()}["Rajesh Kumar"]
    assert full["id_document_number"] == "XXXX-XXXX-1201"

    # echoing the mask back is a no-op; a new number re-queues verification and stays encrypted
    r = client.put("/api/technicians/me", json={"id_document_number": me["id_document_number"]}, headers=rajesh).json()
    assert r["verification_status"] == "verified"
    r = client.put("/api/technicians/me", json={"id_document_number": "ABCD-9999"}, headers=rajesh).json()
    assert r["verification_status"] == "pending" and r["id_document_number"].endswith("9999")
    with engine.connect() as c:
        stored = c.execute(text("SELECT id_document_number FROM technician_profiles WHERE id = :i"), {"i": r["id"]}).scalar()
    assert stored.startswith("gAAAA") and decrypt(stored) == "ABCD-9999"
    assert client.get("/api/technicians/match").json() is not None
    assert "Rajesh Kumar" not in [t["name"] for t in client.get("/api/technicians/match").json()]  # hidden until re-verified


def test_admin_verification_flow(client, admin):
    pending = client.get("/api/admin/technicians", params={"status": "pending"}, headers=admin).json()[0]
    assert client.patch(f"/api/admin/technicians/{pending['id']}/verification", json={"status": "rejected"}, headers=admin).status_code == 422
    r = client.patch(f"/api/admin/technicians/{pending['id']}/verification", json={"status": "verified"}, headers=admin)
    assert r.status_code == 200 and r.json()["verification_status"] == "verified"
    assert pending["id"] in [t["id"] for t in client.get("/api/technicians/match").json()]


def test_admin_metrics_users_and_pagination(client, admin):
    m = client.get("/api/admin/metrics", headers=admin).json()
    assert m["technicians_pending"] == 1 and m["technicians_verified"] == 5 and m["customers"] == 2
    page = client.get("/api/admin/users", params={"limit": 3, "offset": 0}, headers=admin)
    assert len(page.json()) == 3 and int(page.headers["X-Total-Count"]) == m["total_users"]
    assert len(client.get("/api/admin/users", params={"limit": 3, "offset": 9}, headers=admin).json()) == m["total_users"] - 9
    assert client.get("/api/admin/users", params={"limit": 500}, headers=admin).status_code == 422
    victim = next(u for u in page.json() if u["role"] != "admin")
    assert client.patch(f"/api/admin/users/{victim['id']}/status", json={"is_active": False}, headers=admin).json()["is_active"] is False
    admin_user = next(u for u in client.get("/api/admin/users", params={"role": "admin"}, headers=admin).json())
    assert client.patch(f"/api/admin/users/{admin_user['id']}/status", json={"is_active": False}, headers=admin).status_code == 400


def test_admin_manages_categories_and_rules(client, admin):
    cat = client.post("/api/admin/categories", json={"name": "Painting", "icon": "🎨"}, headers=admin)
    assert cat.status_code == 201
    cid = cat.json()["id"]
    assert client.post("/api/admin/categories", json={"name": "Painting"}, headers=admin).status_code == 409
    rules = client.get("/api/admin/rules", params={"category_id": cid}, headers=admin).json()
    assert len(rules) == 1 and rules[0]["is_default"]  # auto fallback rule

    new = {"category_id": cid, "symptom": "Peeling paint", "keywords": "Peeling, Flaking ,peeling", "diagnosis": "Moisture damage",
           "min_price": 900, "max_price": 600, "estimated_minutes": 120}
    assert client.post("/api/admin/rules", json=new, headers=admin).status_code == 422  # min > max
    new["max_price"] = 2500
    rule = client.post("/api/admin/rules", json=new, headers=admin).json()
    assert rule["keywords"] == "peeling,flaking"  # normalised
    out = client.post("/api/services/diagnose", json={"category_id": cid, "description": "paint is peeling off"}).json()
    assert out["diagnosis"] == "Moisture damage"  # engine uses admin-defined rule immediately

    assert client.put(f"/api/admin/rules/{rule['id']}", json={**{k: v for k, v in new.items() if k != "category_id"}, "estimated_minutes": 90}, headers=admin).json()["estimated_minutes"] == 90
    assert client.delete(f"/api/admin/rules/{rules[0]['id']}", headers=admin).status_code == 409  # fallback protected
    assert client.delete(f"/api/admin/rules/{rule['id']}", headers=admin).status_code == 204
    assert client.delete(f"/api/admin/categories/{cid}", headers=admin).status_code == 204
    assert client.delete("/api/admin/categories/1", headers=admin).status_code == 409  # in use


# ------------------------------------------------------------------ platform
def test_health_and_security_headers(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    r = client.get("/api/health/ready")
    assert r.status_code == 200
    assert r.headers["X-Content-Type-Options"] == "nosniff" and r.headers["X-Frame-Options"] == "DENY" and r.headers["X-Request-ID"]
    assert client.get("/api/nope").status_code == 404


def test_production_config_is_validated():
    base = dict(_env_file=None, ENVIRONMENT="production")
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(**base, SECRET_KEY="change-me-in-production", ENCRYPTION_KEY="UJwyoUzZXtDRlqk3BxlKmfWFLkK1h5Zx7HvPVrWtGBk=")
    with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
        Settings(**base, SECRET_KEY="x" * 40, ENCRYPTION_KEY="")
    with pytest.raises(ValueError):
        Settings(ENVIRONMENT="development", _env_file=None, ENCRYPTION_KEY="not-a-valid-fernet-key")
    with pytest.raises(ValueError, match="CORS"):
        Settings(**base, SECRET_KEY="x" * 40, ENCRYPTION_KEY="UJwyoUzZXtDRlqk3BxlKmfWFLkK1h5Zx7HvPVrWtGBk=", CORS_ORIGINS="*")
    ok = Settings(**base, SECRET_KEY="x" * 40, ENCRYPTION_KEY="UJwyoUzZXtDRlqk3BxlKmfWFLkK1h5Zx7HvPVrWtGBk=", CORS_ORIGINS="https://app.example.com")
    assert ok.is_production


@pytest.mark.skipif(not __import__("os").environ.get("TEST_DATABASE_URL"), reason="needs real PostgreSQL row locks")
def test_concurrent_accepts_cannot_double_book(client, customer, customer2, rajesh):
    from concurrent.futures import ThreadPoolExecutor
    from fastapi.testclient import TestClient
    from app.main import app

    a = client.post("/api/bookings", json=booking_body(client, when=future(5, 10)), headers=customer).json()
    b = client.post("/api/bookings", json=booking_body(client, when=future(5, 11)), headers=customer2).json()

    def accept(booking_id):
        with TestClient(app) as c:
            return c.patch(f"/api/bookings/{booking_id}/status", json={"status": "accepted"}, headers=rajesh).status_code

    with ThreadPoolExecutor(2) as pool:
        codes = sorted(pool.map(accept, [a["id"], b["id"]]))
    assert codes == [200, 409]  # the row lock serialises the two requests; one wins, one is refused
