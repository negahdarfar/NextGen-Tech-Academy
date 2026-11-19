import pytest

from nextgen_academy.config import Settings


def test_defaults_are_local_and_safe(monkeypatch):
    for key in ("NEXTGEN_ENV", "NEXTGEN_LOG_LEVEL", "OLLAMA_BASE_URL", "OLLAMA_MODEL"):
        monkeypatch.delenv(key, raising=False)
    settings = Settings.from_env()
    assert settings.ollama_base_url == "http://127.0.0.1:11434"
    assert settings.ollama_model == "qwen2.5:1.5b"


def test_rejects_invalid_log_level(monkeypatch):
    monkeypatch.setenv("NEXTGEN_LOG_LEVEL", "LOUD")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_load_dotenv_does_not_override_process_environment(tmp_path, monkeypatch):
    from nextgen_academy.config import load_dotenv
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=from-file\\nGROQ_API_KEY='quoted-value'\\n", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "from-process")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    load_dotenv(env_file)
    assert __import__("os").environ["GEMINI_API_KEY"] == "from-process"
    assert __import__("os").environ["GROQ_API_KEY"] == "quoted-value"
