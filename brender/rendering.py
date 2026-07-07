import re
import subprocess
from pathlib import Path

from .helpers import get_subprocess_kwargs


def get_scene_names_from_blend(blender_path, blend_file):
    python_expr = (
        "import bpy\n"
        "for scene in bpy.data.scenes:\n"
        "    print('__BRENDER_SCENE__' + scene.name)\n"
    )

    command = [
        blender_path,
        "-b",
        str(blend_file),
        "--python-expr",
        python_expr,
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        **get_subprocess_kwargs(),
    )

    scenes = []

    for line in result.stdout.splitlines():
        if line.startswith("__BRENDER_SCENE__"):
            scene_name = line.replace("__BRENDER_SCENE__", "").strip()
            if scene_name:
                scenes.append(scene_name)

    return scenes


def extract_output_folder_from_blender_line(line):
    extensions = r"(png|jpg|jpeg|exr|tif|tiff|bmp|webp|mp4|avi|mov|mkv)"

    quoted_match = re.search(
        rf"[\"']([^\"']+\.{extensions})[\"']",
        line,
        flags=re.IGNORECASE,
    )

    if quoted_match:
        return Path(quoted_match.group(1)).parent

    drive_match = re.search(
        rf"([A-Za-z]:\\.*?\.{extensions})",
        line,
        flags=re.IGNORECASE,
    )

    if drive_match:
        return Path(drive_match.group(1)).parent

    return None


def get_render_output_folder_from_blender(blender_path, blend_file, scene_name=None):
    scene_repr = repr(scene_name or "")

    python_expr = f"""
import bpy, os
scene_name = {scene_repr}

if scene_name:
    scene = bpy.data.scenes.get(scene_name)
else:
    scene = bpy.context.scene

if scene is None:
    scene = bpy.context.scene

p = bpy.path.abspath(scene.render.filepath)

if not p:
    p = bpy.path.abspath('//')

if p.endswith('/') or p.endswith('\\\\'):
    folder = p
else:
    folder = os.path.dirname(p)

print('__BRENDER_OUTPUT__' + folder)
"""

    command = [
        blender_path,
        "-b",
        str(blend_file),
        "--python-expr",
        python_expr,
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        **get_subprocess_kwargs(),
    )

    for line in result.stdout.splitlines():
        if line.startswith("__BRENDER_OUTPUT__"):
            folder = line.replace("__BRENDER_OUTPUT__", "").strip()
            if folder:
                return Path(folder)

    return None
