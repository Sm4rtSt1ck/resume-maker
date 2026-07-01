from modules.consts import BASE_DIR

CONFIG_DEFAULTS: dict = {
    "auto_open": True,
    "convert_to_pdf": True,
    "template": "classic",
    "output_path": str(BASE_DIR / "output"),
}

# Keys with no default value — displayed as NOT SET when absent
CONFIG_NO_DEFAULT = {"data_file", "last_file"}
