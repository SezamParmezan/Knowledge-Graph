from app.core.config import Settings


def test_settings_default_values():
    settings = Settings(_env_file=None)

    assert settings.app_name == "KnowledgeGraph"
    assert settings.port == 8000
    assert settings.ai_api_model == "gemini-1.5-flash"
    assert settings.is_dev == settings.debug


def test_ensure_dirs_creates_expected_directories(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = Settings(chroma_db_path="data/chroma", cache_path="data/cache")

    settings.ensure_dirs()

    assert (tmp_path / "data" / "chroma").is_dir()
    assert (tmp_path / "data" / "cache").is_dir()
    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / "data").is_dir()
