
from pathlib import Path
from pydantic import BaseModel, Field
from functools import lru_cache

SETTINGS_FILE = "settings.json"


class AppSettings(BaseModel):

    project_dir: Path = Field(default_factory=lambda: Path.cwd())
    output_dir: Path = Field(default_factory=lambda: Path("./output"))
    plugins_dir: Path = Field(default_factory=lambda: Path("./plugins"))
    ams_net_id: str = ""

    @classmethod
    def load_settings(cls) -> "AppSettings":
        settings_file = Path.cwd() / Path(SETTINGS_FILE)
        if settings_file.exists():
            try:
                return cls.model_validate_json(settings_file.read_text())
            except Exception:
                return cls()
        return cls()

    def save_settings(self):
        settings_file = Path.cwd() / Path(SETTINGS_FILE)
        settings_file.write_text(self.model_dump_json(indent=4))


def get_settings(force_reload: bool = False) -> AppSettings:
    if force_reload:
        _get_cached_settings.cache_clear()
    return _get_cached_settings()


@lru_cache()
def _get_cached_settings() -> AppSettings:
    return AppSettings.load_settings()
