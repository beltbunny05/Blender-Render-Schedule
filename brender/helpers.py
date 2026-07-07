import ctypes
import os
import subprocess
import sys
import tkinter.font as tkfont
from pathlib import Path

from .config import ROOT_DIR


def resource_path(relative_path: str) -> Path:
    """Resolve paths for both source execution and PyInstaller bundles."""
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = ROOT_DIR

    return base_path / relative_path


def get_ui_font() -> str:
    preferred_fonts = [
        "Aptos",
        "Segoe UI Variable Display",
        "Segoe UI Variable",
        "Segoe UI",
    ]

    try:
        available_fonts = set(tkfont.families())
        for family in preferred_fonts:
            if family in available_fonts:
                return family
    except Exception:
        pass

    return "Segoe UI"


def clean_path(path: str) -> str:
    return path.strip().strip('"').strip("'")


def normalize_time_input(value: str) -> str:
    """
    Accepts:
    1648 -> 16:48
    930  -> 09:30
    8    -> 08:00
    16:48 -> 16:48
    """
    value = value.strip()

    if value == "":
        return ""

    value = value.replace(" ", "")

    if ":" in value:
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError("Invalid format.")

        hour = int(parts[0])
        minute = int(parts[1])
    else:
        if not value.isdigit():
            raise ValueError("Use only numbers or HH:MM.")

        if len(value) in [1, 2]:
            hour = int(value)
            minute = 0
        elif len(value) == 3:
            hour = int(value[0])
            minute = int(value[1:])
        elif len(value) == 4:
            hour = int(value[:2])
            minute = int(value[2:])
        else:
            raise ValueError("Use something like 1648, 930, 8, or 16:48.")

    if not 0 <= hour <= 23:
        raise ValueError("Invalid hour. Use 00 to 23.")

    if not 0 <= minute <= 59:
        raise ValueError("Invalid minute. Use 00 to 59.")

    return f"{hour:02d}:{minute:02d}"


def apply_windows_modern_effect(window) -> None:
    """Apply dark title bar and attempt Mica on Windows 11."""
    if os.name != "nt":
        return

    try:
        window.update_idletasks()
        hwnd = window.winfo_id()

        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            20,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )

        backdrop_type = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            38,
            ctypes.byref(backdrop_type),
            ctypes.sizeof(backdrop_type),
        )
    except Exception:
        pass


def get_subprocess_kwargs() -> dict:
    """Prevent floating terminal windows on Windows."""
    if os.name != "nt":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": startupinfo,
    }
