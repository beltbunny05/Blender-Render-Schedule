# AGENTS.md

## Project purpose

BRender is a Windows-first desktop app for Blender artists to queue multiple `.blend` files, optionally render all scenes inside each file, schedule renders, monitor logs, and optionally shut down the PC after completion.

## Repository structure

- `brender/app.py`: main CustomTkinter application, UI composition, queue management, render orchestration
- `brender/config.py`: app constants, colors, default Blender path, window settings
- `brender/helpers.py`: font selection, time normalization, Windows UI effects, subprocess helpers, resource path handling
- `brender/rendering.py`: Blender CLI helpers for scene discovery and output-folder parsing
- `brender/__main__.py`: module entry point
- `BRender_App.py`: thin compatibility launcher; keep this file working
- `BRender.spec`: PyInstaller build spec; must remain tracked in Git
- `scripts/build_windows.ps1`: build the Windows executable using `.\.venv\Scripts\python.exe`
- `scripts/package_release.ps1`: package `dist/BRender.exe` plus docs into a versioned release zip
- `docs/INSTALL_WINDOWS.md`: installation guide for non-developers
- `README.md`: portfolio-facing public documentation

## Technologies

- Python 3.10+
- CustomTkinter
- Blender command-line rendering (`blender -b`, `--python-expr`)
- PyInstaller for Windows packaging
- PowerShell scripts for build/release automation

## Commands

### Create local environment

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Run the app

```powershell
.\.venv\Scripts\python.exe BRender_App.py
```

or

```powershell
.\.venv\Scripts\python.exe -m brender
```

### Build Windows executable

```powershell
.\scripts\build_windows.ps1
```

### Package release zip

```powershell
.\scripts\package_release.ps1 -Version 0.1.0
```

## Code and product rules

- Keep the project modular; do not collapse it back into a monolithic single-file app.
- Preserve `BRender_App.py` as a launcher so non-technical users still have a simple entry script.
- Keep the UI text in English unless the user explicitly asks to localize it again.
- Preserve the current queue-location behavior: the UI action opens the folder of the current `.blend` file in the queue, not the render output folder.
- Preserve these core capabilities:
  - add `.blend` files individually
  - add a folder of `.blend`/`.blend1` files
  - scheduled render start
  - render now
  - render all scenes in each `.blend`
  - integrated log/terminal view
  - stop current render
  - optional Windows shutdown after finish
- Keep the project Windows-first unless a change is intentionally broadening platform support.

## Errors that must not be repeated

- Do not ignore `BRender.spec` in `.gitignore`.
- Do not document a release filename that differs from what `scripts/package_release.ps1` actually generates.
- Do not depend on `Activate.ps1` in docs/build instructions; PowerShell execution policy may block it.
- Do not use bare `python` inside build scripts when the project expects `.venv`; use `.\.venv\Scripts\python.exe`.
- Do not publish placeholder repository metadata such as `your-username` without replacing it.

## Important restrictions

- There are currently no automated tests in the repository.
- Build/release validation is Windows-oriented.
- The default Blender path in `brender/config.py` is a convenience value and may not match another machine.
- Automatic shutdown is only implemented for Windows in the current code.

## Validation checklist before considering work complete

For normal app changes:

1. Run the app with `.\.venv\Scripts\python.exe BRender_App.py`.
2. Confirm the UI opens without import/runtime errors.
3. Manually verify the affected workflow in the GUI.
4. Confirm the queue still updates, logging still works, and the launcher still starts the app.

For build/release changes:

1. Run `.\scripts\build_windows.ps1`.
2. Confirm `dist/BRender.exe` is created.
3. Run `.\scripts\package_release.ps1 -Version <version>`.
4. Confirm `dist/BRender-Windows-<version>.zip` is created.
5. Confirm the release package contains:
   - `BRender.exe`
   - `README.md`
   - `INSTALL_WINDOWS.md`

If something cannot be validated locally, state that explicitly in the final response.
