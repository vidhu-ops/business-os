from __future__ import annotations

from fastapi.testclient import TestClient

from backend.auth import create_token, hash_password
from backend.services import analytics_store
from backend.services.geo_ua import classify_source, is_bot_ua, parse_ua, valid_id
from backend.services.user_store import save_users


def test_valid_id_and_ua():
    assert valid_id("abcdefgh")
    assert not valid_id("bad id")
    assert is_bot_ua("Mozilla/5.0 compatible Googlebot")
    parsed = parse_ua("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1")
    assert parsed["device"] == "mobile"
    assert parsed["os"] == "iOS"
    assert classify_source(referrer="", utm_source="", utm_medium="") == "direct"
    assert classify_source(referrer="https://www.google.com/search", utm_source="", utm_medium="") == "organic"
    assert classify_source(referrer="https://linkedin.com/feed", utm_source="", utm_medium="") == "social"


def test_ingest_pageview_heartbeat_signup(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANALYTICS_DB_PATH", str(tmp_path / "analytics.sqlite"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    analytics_store._pg_ready = False

    first = analytics_store.ingest(
        {
            "type": "pageview",
            "visitor_id": "visitorabc123",
            "session_id": "sessionabc123",
            "path": "/",
            "href": "https://iidatech.biz/?utm_source=linkedin&utm_medium=social",
            "referrer": "https://www.linkedin.com/feed",
            "utm_source": "linkedin",
            "utm_medium": "social",
            "country": "IN",
            "country_name": "India",
            "city": "Bengaluru",
            "place": "Bengaluru, India",
            "device": "desktop",
            "browser": "Chrome",
            "source": "social",
        }
    )
    assert first["ok"] is True
    pageview_id = first["pageview_id"]
    analytics_store.ingest(
        {
            "type": "heartbeat",
            "visitor_id": "visitorabc123",
            "session_id": "sessionabc123",
            "pageview_id": pageview_id,
            "path": "/",
            "duration_ms": 15000,
            "scroll_pct": 40,
        }
    )
    analytics_store.ingest(
        {
            "type": "pageview",
            "visitor_id": "visitorabc123",
            "session_id": "sessionabc123",
            "path": "/pricing",
        }
    )
    analytics_store.identify("visitorabc123", "sessionabc123", "founder@example.com", event_name="signup")

    data = analytics_store.overview(7)
    assert data["totals"]["visitors"] == 1
    assert data["totals"]["pageviews"] == 2
    assert data["totals"]["signups"] == 1
    paths = {row["path"] for row in data["top_pages"]}
    assert "/" in paths
    assert "/pricing" in paths
    detail = analytics_store.session_detail("sessionabc123")
    assert detail is not None
    assert detail["session"]["user_email"] == "founder@example.com"
    assert detail["pages"][0]["duration_ms"] >= 15000
    attr = analytics_store.attribution_for_visitor("visitorabc123")
    assert attr["utm_source"] == "linkedin"
    assert attr["city"] == "Bengaluru"


def test_collect_and_admin_overview(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANALYTICS_DB_PATH", str(tmp_path / "analytics.sqlite"))
    monkeypatch.setenv("USER_DB_PATH", str(tmp_path / "users.sqlite"))
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    analytics_store._pg_ready = False

    save_users(
        {
            "admin@example.com": {
                "email": "admin@example.com",
                "name": "Admin",
                "password_hash": hash_password("secret12"),
                "created_at": "2026-08-01T00:00:00Z",
                "plan": "starter",
            }
        }
    )

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.routers.analytics import admin_router, public_router

    app = FastAPI()
    app.include_router(public_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")
    from backend.routers.analytics import leads_router
    app.include_router(leads_router, prefix="/api/v1")
    client = TestClient(app)
    collected = client.post(
        "/api/v1/analytics/collect",
        json={
            "visitor_id": "vid12345678",
            "session_id": "sid12345678",
            "type": "pageview",
            "path": "/about",
            "title": "About",
            "href": "https://iidatech.biz/about",
            "referrer": "https://google.com/",
            "utm": {"source": "google", "medium": "organic"},
            "client": {"timezone": "Asia/Kolkata", "language": "en-IN", "screen_w": 1440, "screen_h": 900},
        },
        headers={"CF-IPCountry": "IN", "CF-IPCity": "Mumbai", "User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"},
    )
    assert collected.status_code == 200
    assert collected.json()["ok"] is True

    denied = client.get("/api/v1/admin/analytics/overview")
    assert denied.status_code in {401, 403}

    token = create_token("admin@example.com")
    ok = client.get("/api/v1/admin/analytics/overview?days=7", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200
    body = ok.json()
    assert body["totals"]["pageviews"] >= 1
    sessions = client.get("/api/v1/admin/analytics/sessions?days=7", headers={"Authorization": f"Bearer {token}"})
    assert sessions.status_code == 200
    assert sessions.json()["total"] >= 1

    people = client.get(
        "/api/v1/admin/analytics/pages/people?path=/about&days=7",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert people.status_code == 200
    assert people.json()["unique_visitors"] >= 1

    leads = client.get("/api/v1/admin/leads", headers={"Authorization": f"Bearer {token}"})
    assert leads.status_code == 200
    assert leads.json()["total"] >= 1
    emails = {row.get("email") for row in leads.json()["leads"]}
    assert "admin@example.com" in emails
    assert body["totals"]["registered_users"] >= 1

    uploaded = client.post(
        "/api/v1/admin/leads/import",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("leads.csv", "email,name,company,source\nfounder@import.test,Imported Founder,Acme,sheet\n", "text/csv")},
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["created"] >= 1


def test_demo_journey_and_page_people(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANALYTICS_DB_PATH", str(tmp_path / "analytics.sqlite"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    analytics_store._pg_ready = False
    analytics_store.ingest(
        {
            "type": "pageview",
            "visitor_id": "demovisitor01",
            "session_id": "demosession01",
            "path": "/app/research",
            "href": "https://iidatech.biz/app/research?project=demo_readonly",
            "props": {"is_demo": True},
        }
    )
    analytics_store.ingest(
        {
            "type": "pageview",
            "visitor_id": "demovisitor01",
            "session_id": "demosession01",
            "path": "/app/team",
            "href": "https://iidatech.biz/app/team?project=demo_readonly",
            "is_demo": True,
        }
    )
    overview = analytics_store.overview(7)
    assert overview["totals"]["demo_starts"] >= 1
    assert any(part["label"] == "Research" for part in overview["demo"]["parts"])
    people = analytics_store.page_people("/app/research?project=demo_readonly", 7)
    assert people["unique_visitors"] == 1
    leads = analytics_store.list_leads()
    assert leads["total"] >= 1
    assert leads["leads"][0]["saw_demo"] is True
    journey = analytics_store.visitor_journey("demovisitor01")
    assert journey is not None
    assert len(journey["journey"]) == 2


def test_existing_users_backfill_into_leads(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ANALYTICS_DB_PATH", str(tmp_path / "analytics.sqlite"))
    monkeypatch.setenv("USER_DB_PATH", str(tmp_path / "users.sqlite"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    analytics_store._pg_ready = False
    save_users(
        {
            "founder@old.test": {
                "email": "founder@old.test",
                "name": "Priya",
                "created_at": "2026-01-15T00:00:00Z",
                "signup_attribution": {"source": "organic", "place": "Mumbai, India"},
            },
            "demo@local": {"email": "demo@local", "name": "Demo"},
        }
    )
    overview = analytics_store.overview(7)
    assert overview["totals"]["registered_users"] == 1
    leads = analytics_store.list_leads()
    emails = {row["email"] for row in leads["leads"]}
    assert "founder@old.test" in emails
    assert "demo@local" not in emails
    founder = next(row for row in leads["leads"] if row["email"] == "founder@old.test")
    assert founder["signed_up"] is True
    assert founder["status"] == "signed_up"
    assert founder["name"] == "Priya"
