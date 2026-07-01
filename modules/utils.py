import sys
import os
import tempfile
import webbrowser
import subprocess
import json

from pathlib import Path

from modules.consts import BASE_DIR
from modules.defaults import CONFIG_DEFAULTS


def clickable_path(path: str | Path) -> str:
    abs_path = Path(path).resolve()
    uri = abs_path.as_uri()
    return f"\033]8;;{uri}\033\\{abs_path}\033]8;;\033\\"


def _save_config(config: dict) -> None:
    config_path = BASE_DIR / "config.json"
    fd, tmp_path = tempfile.mkstemp(dir=config_path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        os.replace(tmp_path, config_path)
    except Exception:
        os.unlink(tmp_path)
        raise


def write_config(config: dict, key: str, value) -> None:
    config[key] = str(value) if isinstance(value, Path) else value
    _save_config(config)


def remove_from_config(config: dict, key: str) -> None:
    config.pop(key)
    _save_config(config)


def open_browser(config, path: str | Path) -> None:
    if not config.get("auto_open", CONFIG_DEFAULTS["auto_open"]):
        return
    path_obj = Path(path).resolve()
    if sys.platform == 'win32':
        os.startfile(str(path_obj))
    else:
        file_url = path_obj.as_uri()
        if sys.platform == 'darwin':
            subprocess.Popen(['open', file_url])
        else:
            try:
                subprocess.Popen(['xdg-open', file_url])
            except OSError:
                webbrowser.open(file_url)


def get_photo_from_resume(path: str | Path) -> str:
    with open(path, "r") as f:
        resume = json.load(f)
        photo_path = resume["photo"]
        return photo_path
