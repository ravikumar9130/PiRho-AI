"""Tests for billing/promo code endpoints."""
import pytest
from unittest.mock import MagicMock


class TestPromoEndpoints:
    """Test promo code API endpoints."""

    def test_list_plans(self, client, mock_supabase):
        """Test listing available plans."""
        response = client.get("/api/v1/billing/plans")
        
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) == 4
        
        plan_ids = [p["id"] for p in data["plans"]]
        assert "free" in plan_ids
        assert "starter" in plan_ids
        assert "pro" in plan_ids
        assert "fund" in plan_ids
        
        # Check Pro plan has promo_available flag
        pro_plan = next(p for p in data["plans"] if p["id"] == "pro")
        assert pro_plan.get("promo_available") is True

    def test_plans_have_required_fields(self, client, mock_supabase):
        """Test that all plans have required fields."""
        response = client.get("/api/v1/billing/plans")
        
        assert response.status_code == 200
        for plan in response.json()["plans"]:
            assert "id" in plan
            assert "name" in plan
            assert "price" in plan
            assert "features" in plan
            assert isinstance(plan["features"], list)
