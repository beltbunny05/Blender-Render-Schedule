from pathlib import Path


APP_TITLE = "Blender Render Queue"
WINDOW_SIZE = "1240x800"
MIN_WINDOW_SIZE = (1050, 700)
DEFAULT_BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
ICON_FILENAME = "blender.ico"
ROOT_DIR = Path(__file__).resolve().parent.parent

COLORS = {
    "bg": "#0D0E10",
    "card": "#14161A",
    "card_2": "#101215",
    "border": "#23262D",
    "text": "#F3F4F6",
    "muted": "#A6ADB8",
    "accent": "#F5792A",
    "accent_hover": "#D9671D",
    "accent_soft": "#2B1C12",
    "danger": "#B3472D",
    "danger_hover": "#963A24",
    "terminal_bg": "#0A0B0D",
    "terminal_text": "#E8EAF0",
}
