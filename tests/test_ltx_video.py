from nextgen_academy.ltx_video import LTXClient


def client(budget=1.44):
    return LTXClient("test-key", max_spend_usd=budget)


def test_ltx_fast_720p_estimated_cost_is_per_second():
    assert client().estimated_clip_cost == 0.72


def test_budget_limits_number_of_generated_scenes():
    worker = client(1.44)
    assert worker.allowed_clip_count(1.44, 20) == 2
    assert worker.allowed_clip_count(1.0, 20) == 1
    assert worker.allowed_clip_count(0.71, 20) == 0


def test_scene_limit_is_respected():
    assert client(10).allowed_clip_count(10, 3) == 3


def test_ltx_disabled_without_api_key_or_positive_budget(monkeypatch):
    monkeypatch.delenv("LTX_API_KEY", raising=False)
    monkeypatch.setenv("LTX_MAX_SPEND_USD", "100")
    assert LTXClient.from_env() is None
    monkeypatch.setenv("LTX_API_KEY", "dummy")
    monkeypatch.setenv("LTX_MAX_SPEND_USD", "0")
    assert LTXClient.from_env() is None
