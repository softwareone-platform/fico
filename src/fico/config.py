import json
from pathlib import Path
from typing import Any


class Config:
    def __init__(self):
        self.config_file_path = Path("~").expanduser() / ".fico"
        self.config_file_path.mkdir(exist_ok=True)
        self.config = {}
        self.load_config()

    def get_access_token(self) -> str | None:
        credentials = self.config.setdefault("credentials", {})
        return credentials.get(self.get_last_used_account()["id"])

    def is_configured(self) -> bool:
        return bool(self.config)

    def get_refresh_token(self) -> str | None:
        credentials = self.config.setdefault("credentials", {})
        return credentials.get("refresh_token")

    def set_credentials(self, access_token: str, refresh_token: str) -> None:
        credentials = self.config.setdefault("credentials", {})
        credentials[self.get_last_used_account()["id"]] = access_token
        credentials["refresh_token"] = refresh_token
        self.save_config()

    def set_last_used_account(self, account: dict[str, Any]) -> None:
        self.config["last_used_account"] = account
        self.save_config()

    def get_last_used_account(self) -> dict[str, Any]:
        return self.config["last_used_account"]

    def set_user(self, user: dict[str, Any]) -> None:
        self.config["user"] = user

    def get_user(self) -> dict[str, Any]:
        return self.config["user"]

    def get_url(self) -> str:
        return self.config["url"]

    def set_url(self, url: str) -> None:
        self.config["url"] = url
        self.save_config()

    def load_config(self) -> None:
        try:
            with open(self.config_file_path / "config.json") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {}

    def save_config(self) -> None:
        with open(self.config_file_path/ "config.json", "w") as f:
            json.dump(self.config, f)

    def delete(self) -> None:
        self.config = {}
        config_file = self.config_file_path / "config.json"
        config_file.unlink()
