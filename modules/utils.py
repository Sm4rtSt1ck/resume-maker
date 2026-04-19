import json

from pathlib import Path

from modules.consts import BASE_DIR


def clickable_path(path: str | Path) -> str:
    abs_path = Path(path).resolve()
    uri = abs_path.as_uri()
    return f"\033]8;;{uri}\033\\{abs_path}\033]8;;\033\\"


def write_config(config: dict, key: str, value) -> None:
    config[key] = value
    with open(BASE_DIR / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def remove_from_config(config: dict, key: str) -> None:
    config.pop(key)
    with open(BASE_DIR / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
