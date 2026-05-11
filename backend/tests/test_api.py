"""Tests for HustleScale API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import auth


@pytest.fixture(autouse=True)
def init_database():
    """Ensure database tables exist before each test."""
    auth.init_db()


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "hustle-scale"


class TestDomainsEndpoint:
    def test_list_domains(self, client):
        response = client.get("/v1/domains")
        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert len(data["domains"]) == 8
        domain_ids = {d["id"] for d in data["domains"]}
        assert "business_plan" in domain_ids
        assert "funding" in domain_ids
        assert "market_prices" in domain_ids

    def test_domain_structure(self, client):
        response = client.get("/v1/domains")
        for domain in response.json()["domains"]:
            assert "id" in domain
            assert "name" in domain
            assert "description" in domain
            assert "icon" in domain


class TestMarketPricesEndpoint:
    def test_categories(self, client):
        response = client.get("/v1/market-prices/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_search_prices(self, client):
        response = client.post(
            "/v1/market-prices",
            json={"category": "poultry"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "prices" in data
        assert "last_updated" in data


class TestBusinessDoctorEndpoint:
    def test_doctor_analysis(self, client):
        response = client.post(
            "/v1/business-doctor",
            json={
                "business_type": "poultry",
                "monthly_revenue_ugx": 1000000,
                "monthly_costs_ugx": 600000,
                "months_operating": 6,
                "employees": 1,
                "location": "Kampala",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "health_score" in data
        assert "diagnosis" in data
        assert "quick_wins" in data
        assert 0 <= data["health_score"] <= 100

    def test_doctor_zero_values(self, client):
        response = client.post(
            "/v1/business-doctor",
            json={
                "business_type": "general",
                "monthly_revenue_ugx": 0,
                "monthly_costs_ugx": 0,
                "months_operating": 0,
                "employees": 0,
                "location": "",
            },
        )
        assert response.status_code == 200


class TestFundingEndpoint:
    def test_list_all_funding(self, client):
        response = client.get("/v1/funding/all")
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert len(data["sources"]) >= 6

    def test_match_funding(self, client):
        response = client.post(
            "/v1/funding/match",
            json={
                "business_type": "poultry",
                "location": "Kampala",
                "capital_needed_ugx": 2000000,
                "stage": "planning",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert "total_available" in data


class TestImpactEndpoint:
    def test_impact_stats(self, client):
        response = client.get("/v1/impact")
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "businesses_planned" in data
        assert "businesses_launched" in data
        assert "jobs_created" in data


class TestLeaderboardEndpoint:
    def test_leaderboard(self, client):
        response = client.get("/v1/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert len(data["entries"]) >= 1
        assert "total_entrepreneurs" in data


class TestAuthEndpoints:
    def test_signup_login_flow(self, client):
        import time
        email = f"test_{int(time.time())}@example.com"

        # Signup
        response = client.post(
            "/v1/auth/signup",
            json={
                "email": email,
                "password": "test123456",
                "name": "Test User",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user_id" in data
        assert data["credits"] > 0

        token = data["token"]

        # Login
        response = client.post(
            "/v1/auth/login",
            json={"email": email, "password": "test123456"},
        )
        assert response.status_code == 200
        assert "token" in response.json()

        # Me endpoint
        response = client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_login_wrong_password(self, client):
        response = client.post(
            "/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_me_no_token(self, client):
        response = client.get("/v1/auth/me")
        assert response.status_code == 401


class TestFeedbackEndpoint:
    def test_submit_feedback(self, client):
        response = client.post(
            "/v1/feedback",
            json={
                "message_id": "test-msg-123",
                "rating": 1,
                "comment": "Very helpful advice!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
