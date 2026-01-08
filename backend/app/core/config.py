from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="VideoMRP v2", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=5000, alias="APP_PORT")

    data_dir: str = Field(default="./data", alias="DATA_DIR")
    db_url: str = Field(default="sqlite:///./data/app.db", alias="DB_URL")

    ffmpeg_bin: str = Field(default="ffmpeg", alias="FFMPEG_BIN")
    ffprobe_bin: str = Field(default="ffprobe", alias="FFPROBE_BIN")

    translate_provider: str = Field(default="libretranslate", alias="TRANSLATE_PROVIDER")
    libretranslate_url: str = Field(default="http://localhost:5001/translate", alias="LIBRETRANSLATE_URL")
    libretranslate_api_key: str = Field(default="", alias="LIBRETRANSLATE_API_KEY")
    enable_argos_translate: bool = Field(default=True, alias="ENABLE_ARGOS_TRANSLATE")

    tts_provider: str = Field(default="piper", alias="TTS_PROVIDER")
    piper_bin: str = Field(default="piper", alias="PIPER_BIN")
    piper_model_path: str = Field(default="", alias="PIPER_MODEL_PATH")

    enable_subtitles: bool = Field(default=True, alias="ENABLE_SUBTITLES")
    enable_voiceover: bool = Field(default=True, alias="ENABLE_VOICEOVER")
    enable_scene_detect: bool = Field(default=False, alias="ENABLE_SCENE_DETECT")

    allow_non_file_url: bool = Field(default=False, alias="ALLOW_NON_FILE_URL")

settings = Settings()
