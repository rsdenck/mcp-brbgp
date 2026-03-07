import configparser
import os
from pathlib import Path

_config = None


def load_config(config_path: str = None) -> configparser.ConfigParser:
    global _config

    if _config is not None:
        return _config

    _config = configparser.ConfigParser()

    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.conf")

    if os.path.exists(config_path):
        _config.read(config_path)
    else:
        _config["database"] = {"path": "./brbgp.db"}
        _config["server"] = {"host": "0.0.0.0", "port": "8000"}
        _config["cloudflare"] = {"api_token": "", "account_id": ""}
        _config["ollama"] = {
            "enabled": "false",
            "base_url": "http://localhost:11434",
            "model": "llama3",
        }
        _config["notifications"] = {
            "telegram_enabled": "false",
            "webhook_enabled": "false",
        }

    return _config


def get_config() -> configparser.ConfigParser:
    if _config is None:
        return load_config()
    return _config


def get_database_url() -> str:
    cfg = get_config()
    db_path = cfg.get("database", "path", fallback="./brbgp.db")
    return f"sqlite+aiosqlite:///{db_path}"


def get_server_host() -> str:
    return get_config().get("server", "host", fallback="0.0.0.0")


def get_server_port() -> int:
    return int(get_config().get("server", "port", fallback="8000"))


def get_cloudflare_token() -> str:
    return get_config().get("cloudflare", "api_token", fallback="")


def get_cloudflare_account_id() -> str:
    return get_config().get("cloudflare", "account_id", fallback="")


def is_ollama_enabled() -> bool:
    return get_config().get("ollama", "enabled", fallback="false").lower() == "true"


def get_ollama_url() -> str:
    return get_config().get("ollama", "base_url", fallback="http://localhost:11434")


def get_ollama_model() -> str:
    return get_config().get("ollama", "model", fallback="llama3")
