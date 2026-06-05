from app.core.config import Settings


def test_settings_provides_default_runtime_values():
    settings = Settings()

    assert settings.app_name == "voice_translation_agent"
    assert settings.app_version == "0.1.0"
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.default_source_language == "en"
    assert settings.default_target_language == "zh"
    assert settings.ffmpeg_binary == "ffmpeg"
    assert settings.asr_model == "fun-asr-realtime"
    assert settings.dashscope_websocket_url == "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
    assert settings.dashscope_api_key is None
    assert settings.llm_model == "qwen-turbo"
    assert settings.llm_base_url == "https://api.qnaigc.com/v1"
    assert settings.llm_api_key is None
    assert settings.use_real_worker is False


def test_settings_reads_environment_overrides(monkeypatch):
    monkeypatch.setenv("APP_NAME", "custom_service")
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    monkeypatch.setenv("DEFAULT_SOURCE_LANGUAGE", "ja")
    monkeypatch.setenv("DEFAULT_TARGET_LANGUAGE", "zh")
    monkeypatch.setenv("FFMPEG_BINARY", "custom-ffmpeg")
    monkeypatch.setenv("ASR_MODEL", "custom-asr")
    monkeypatch.setenv("DASHSCOPE_WEBSOCKET_URL", "wss://example.test/asr")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "secret")
    monkeypatch.setenv("LLM_MODEL", "custom-llm")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "llm-secret")
    monkeypatch.setenv("USE_REAL_WORKER", "true")

    settings = Settings()

    assert settings.app_name == "custom_service"
    assert settings.app_version == "1.2.3"
    assert settings.cors_origins == [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    assert settings.default_source_language == "ja"
    assert settings.default_target_language == "zh"
    assert settings.ffmpeg_binary == "custom-ffmpeg"
    assert settings.asr_model == "custom-asr"
    assert settings.dashscope_websocket_url == "wss://example.test/asr"
    assert settings.dashscope_api_key == "secret"
    assert settings.llm_model == "custom-llm"
    assert settings.llm_base_url == "https://example.test/v1"
    assert settings.llm_api_key == "llm-secret"
    assert settings.use_real_worker is True


def test_settings_reads_values_from_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("USE_REAL_WORKER", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_NAME=file_service\n"
        "CORS_ORIGINS=http://localhost:5173,http://localhost:4173\n"
        "USE_REAL_WORKER=true\n",
        encoding="utf-8",
    )

    settings = Settings(env_file=env_file)

    assert settings.app_name == "file_service"
    assert settings.cors_origins == ["http://localhost:5173", "http://localhost:4173"]
    assert settings.use_real_worker is True


def test_environment_variables_override_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_NAME=file_service\n", encoding="utf-8")
    monkeypatch.setenv("APP_NAME", "environment_service")

    settings = Settings(env_file=env_file)

    assert settings.app_name == "environment_service"
