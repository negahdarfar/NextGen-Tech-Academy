import pytest

from nextgen_academy.vidogrid import VidoGridSettings


def test_loads_key_from_local_dotenv(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VIDOGRID_API_KEY", raising=False)
    (tmp_path / ".env").write_text(
        "VIDOGRID_API_KEY=test-secret\nVIDOGRID_DURATION_SECONDS=15\n",
        encoding="utf-8",
    )
    settings = VidoGridSettings.from_env()
    assert settings.api_key == "test-secret"
    assert settings.duration_seconds == 15
    assert settings.endpoint.endswith("grok-imagine-video-1.5-lite")


def test_requires_api_key(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VIDOGRID_API_KEY", raising=False)
    with pytest.raises(ValueError, match="VIDOGRID_API_KEY"):
        VidoGridSettings.from_env()


def test_rejects_duration_above_15_seconds(monkeypatch):
    monkeypatch.setenv("VIDOGRID_API_KEY", "test-secret")
    monkeypatch.setenv("VIDOGRID_DURATION_SECONDS", "16")
    with pytest.raises(ValueError, match="between 1 and 15"):
        VidoGridSettings.from_env()
