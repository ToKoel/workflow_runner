
from pathlib import Path
from pydantic import BaseModel, Field
from functools import lru_cache

SETTINGS_FILE = "settings.json"


class AppSettings(BaseModel):

    project_dir: Path = Field(default_factory=lambda: Path.cwd())
    output_dir: Path = Field(default_factory=lambda: Path("./output"))
    plugins_dir: Path = Field(default_factory=lambda: Path("./plugins"))
    ams_net_id: str = ""

    def load_settings(self):
        settings_file = Path.cwd() / Path(SETTINGS_FILE)
        if settings_file.exists():
            settings_from_file = settings_file.read_text()
            AppSettings.model_validate_json(settings_from_file)

    def save_settings(self):
        settings_file = Path.cwd() / Path(SETTINGS_FILE)
        settings_file.write_text(self.settings.model_dump_json())


@lru_cache()
def get_settings() -> AppSettings:
    settings = AppSettings()
    settings.load_settings()
    return settings
