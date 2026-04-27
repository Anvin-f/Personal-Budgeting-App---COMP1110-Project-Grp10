import json
import os
from copy import deepcopy


SETTINGS_FILE = "data/settings.json"

DEFAULT_SETTINGS = {
    "dark_mode": False,
    "compact_tables": False,
    "show_filter_chips": True,
    "confirm_delete": True,
}


def _normalize_settings(data):
    settings = deepcopy(DEFAULT_SETTINGS)
    if isinstance(data, dict):
        for key in settings:
            if key in data:
                settings[key] = bool(data[key])
    return settings


def read_settings():
    if not os.path.exists(SETTINGS_FILE):
        return deepcopy(DEFAULT_SETTINGS)

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file_handle:
            raw = json.load(file_handle)
    except (OSError, json.JSONDecodeError):
        return deepcopy(DEFAULT_SETTINGS)

    return _normalize_settings(raw)


def write_settings(settings):
    normalized = _normalize_settings(settings)
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file_handle:
        json.dump(normalized, file_handle, indent=2)
    return normalized


def update_settings(**kwargs):
    current = read_settings()
    current.update(kwargs)
    return write_settings(current)
