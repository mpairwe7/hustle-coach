"""Auth system tests — signup, login, tokens, credits, milestones, profiles, feedback."""

import os
import tempfile
import time
import uuid

import pytest

from app import auth


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch):
    """Point auth module at a temporary DB for every test."""
    db_path = os.path.join(
        os.path.dirname(__file__), f".test_auth_{uuid.uuid4().hex[:8]}.db"
    )
    monkeypatch.setattr(auth, "DB_PATH", db_path)
    auth.init_db()
    yield
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass
    # WAL and SHM files
    for suffix in ("-wal", "-shm"):
        try:
            os.unlink(db_path + suffix)
        except OSError:
            pass


# ── Signup ──


class TestSignup:
    def test_signup_returns_token_and_credits(self):
        result = auth.signup("test@example.com", "password123", "Test User")
        assert "token" in result
        assert "user_id" in result
        assert result["credits"] == auth.FREE_CREDITS

    def test_signup_duplicate_email_raises(self):
        auth.signup("dup@example.com", "pass1", "User 1")
        with pytest.raises(ValueError, match="already registered"):
            auth.signup("dup@example.com", "pass2", "User 2")

    def test_signup_normalises_email_case(self):
        auth.signup("Upper@Example.COM", "pass", "User")
        with pytest.raises(ValueError):
            auth.signup("upper@example.com", "pass", "Dup")

    def test_signup_creates_default_milestones(self):
        result = auth.signup("ms@example.com", "pass", "MS User")
        milestones = auth.get_milestones(result["user_id"])
        assert len(milestones) == 12
        assert all(m["completed"] == 0 for m in milestones)

    def test_signup_with_optional_fields(self):
        result = auth.signup(
            "full@example.com", "pass", "Full User",
            business_type="poultry", location="Kampala", age=25,
        )
        user = auth.get_user(result["user_id"])
        assert user is not None
        assert user["business_type"] == "poultry"
        assert user["location"] == "Kampala"
        assert user["age"] == 25


# ── Login ──


class TestLogin:
    def test_login_success(self):
        auth.signup("login@example.com", "mypassword", "Login User")
        result = auth.login("login@example.com", "mypassword")
        assert "token" in result
        assert "user_id" in result

    def test_login_wrong_password(self):
        auth.signup("wrong@example.com", "correctpass", "User")
        with pytest.raises(ValueError, match="Invalid"):
            auth.login("wrong@example.com", "wrongpass")

    def test_login_nonexistent_email(self):
        with pytest.raises(ValueError, match="Invalid"):
            auth.login("ghost@example.com", "password")

    def test_login_preserves_credits(self):
        auth.signup("credits@example.com", "pass", "C")
        result = auth.login("credits@example.com", "pass")
        assert result["credits"] == auth.FREE_CREDITS


# ── Token verification ──


class TestTokenVerification:
    def test_valid_token_verifies(self):
        signup = auth.signup("token@example.com", "pass123", "Token User")
        payload = auth.verify_token(signup["token"])
        assert payload is not None
        assert payload["sub"] == signup["user_id"]
        assert payload["email"] == "token@example.com"

    def test_invalid_token_returns_none(self):
        assert auth.verify_token("invalid.token.here") is None

    def test_empty_token_returns_none(self):
        assert auth.verify_token("") is None


# ── Credits ──


class TestCredits:
    def test_deduct_credit(self):
        result = auth.signup("dc@example.com", "pass", "DC")
        uid = result["user_id"]
        user_before = auth.get_user(uid)
        assert user_before["credits"] == auth.FREE_CREDITS

        ok = auth.deduct_credit(uid)
        assert ok is True

        user_after = auth.get_user(uid)
        assert user_after["credits"] == auth.FREE_CREDITS - 1

    def test_deduct_credit_refuses_when_zero(self):
        result = auth.signup("zero@example.com", "pass", "Z")
        uid = result["user_id"]
        # Exhaust all credits
        for _ in range(auth.FREE_CREDITS):
            auth.deduct_credit(uid)
        assert auth.deduct_credit(uid) is False

    def test_deduct_credit_nonexistent_user(self):
        assert auth.deduct_credit("nonexistent-user-id") is False


# ── User retrieval ──


class TestGetUser:
    def test_get_user_found(self):
        result = auth.signup("found@example.com", "pass", "Found")
        user = auth.get_user(result["user_id"])
        assert user is not None
        assert user["email"] == "found@example.com"
        assert user["name"] == "Found"

    def test_get_user_not_found(self):
        assert auth.get_user("nonexistent") is None


# ── Milestones ──


class TestMilestones:
    def test_update_milestone_complete(self):
        result = auth.signup("mile@example.com", "pass", "M")
        uid = result["user_id"]
        milestones = auth.get_milestones(uid)
        mid = milestones[0]["id"]

        assert auth.update_milestone(uid, mid, completed=True) is True
        updated = auth.get_milestones(uid)
        first = [m for m in updated if m["id"] == mid][0]
        assert first["completed"] == 1
        assert first["completed_at"] is not None

    def test_update_milestone_uncomplete(self):
        result = auth.signup("unm@example.com", "pass", "U")
        uid = result["user_id"]
        milestones = auth.get_milestones(uid)
        mid = milestones[0]["id"]

        auth.update_milestone(uid, mid, completed=True)
        auth.update_milestone(uid, mid, completed=False)
        updated = auth.get_milestones(uid)
        first = [m for m in updated if m["id"] == mid][0]
        assert first["completed"] == 0

    def test_update_milestone_wrong_user(self):
        r1 = auth.signup("u1@example.com", "pass", "U1")
        r2 = auth.signup("u2@example.com", "pass", "U2")
        mid = auth.get_milestones(r1["user_id"])[0]["id"]
        # User 2 should not update user 1's milestone
        assert auth.update_milestone(r2["user_id"], mid) is False

    def test_update_milestone_invalid_id(self):
        result = auth.signup("inv@example.com", "pass", "I")
        assert auth.update_milestone(result["user_id"], "fake-id") is False


# ── Business profiles ──


class TestBusinessProfile:
    def test_create_profile(self):
        result = auth.signup("bp@example.com", "pass", "BP")
        uid = result["user_id"]
        assert auth.get_business_profile(uid) is None

        profile = auth.upsert_business_profile(uid, {
            "business_name": "My Poultry",
            "business_type": "poultry",
            "location": "Kampala",
            "startup_capital_ugx": 2000000,
            "employees": 1,
            "stage": "launched",
        })
        assert profile["business_name"] == "My Poultry"
        assert profile["stage"] == "launched"

    def test_update_profile(self):
        result = auth.signup("upd@example.com", "pass", "UPD")
        uid = result["user_id"]
        auth.upsert_business_profile(uid, {"business_name": "Old Name"})
        updated = auth.upsert_business_profile(uid, {"business_name": "New Name"})
        assert updated["business_name"] == "New Name"


# ── Impact stats ──


class TestImpactStats:
    def test_impact_stats_structure(self):
        stats = auth.get_impact_stats()
        assert "total_users" in stats
        assert "businesses_planned" in stats
        assert "businesses_launched" in stats
        assert "jobs_created" in stats
        assert "total_capital_mobilised_ugx" in stats
        assert "regions_reached" in stats
        assert "milestones_completed" in stats

    def test_impact_counts_users(self):
        auth.signup("st1@example.com", "pass", "S1")
        auth.signup("st2@example.com", "pass", "S2")
        stats = auth.get_impact_stats()
        assert stats["total_users"] >= 2


# ── Feedback ──


class TestFeedback:
    def test_save_feedback(self):
        # Should not raise
        auth.save_feedback("msg-1", rating=1, comment="Great!", user_id="u1")
        auth.save_feedback("msg-2", rating=-1, comment="Bad", user_id="")
