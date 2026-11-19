import pytest

from nextgen_academy.automation import _require_free_credit_budget


def test_credit_guard_requires_separate_free_balance(monkeypatch):
    monkeypatch.setenv("VIDOGRID_CREDITS_PER_CLIP", "2")
    with pytest.raises(RuntimeError, match="separate free/trial"):
        _require_free_credit_budget({"balance": 100}, clips=4)


def test_credit_guard_allows_only_sufficient_free_balance(monkeypatch):
    monkeypatch.setenv("VIDOGRID_CREDITS_PER_CLIP", "2")
    _require_free_credit_budget({"account": {"free_credits": 8}}, clips=4)
    with pytest.raises(RuntimeError, match="Insufficient free"):
        _require_free_credit_budget({"free_credits": 7}, clips=4)


def test_credit_guard_requires_configured_cost(monkeypatch):
    monkeypatch.delenv("VIDOGRID_CREDITS_PER_CLIP", raising=False)
    with pytest.raises(RuntimeError, match="VIDOGRID_CREDITS_PER_CLIP"):
        _require_free_credit_budget({"free_credits": 100}, clips=4)
