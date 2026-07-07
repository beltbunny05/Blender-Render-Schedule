# CHANGELOG_DEV.md

## During this Codex conversation

### 1. UI review and UX cleanup

- Reviewed the original monolithic UI in `BRender_App.py`
- Reorganized the action area into three workflow-oriented sections:
  - Build queue
  - Start render
  - Control and power
- Aligned the UI with a cleaner, more portfolio-ready workflow

### 2. Queue location behavior changed

- Replaced the previous behavior that opened the current render output location
- Implemented a new action that opens the folder of the current queued `.blend` file
- Added fallback behavior to use the first queued file when nothing is actively rendering

### 3. UI and app text converted to English

- Converted interface text to English
- Converted user-facing messages to English
- Converted core public documentation to English
- Introduced a more modern font selection strategy with fallbacks:
  - Aptos
  - Segoe UI Variable Display
  - Segoe UI Variable
  - Segoe UI

### 4. Monolith refactor into package structure

- Replaced the large root app implementation with a modular package:
  - `brender/app.py`
  - `brender/config.py`
  - `brender/helpers.py`
  - `brender/rendering.py`
  - `brender/__init__.py`
  - `brender/__main__.py`
- Reduced `BRender_App.py` to a thin launcher
- Added packaging metadata:
  - `pyproject.toml`
  - `requirements.txt`
  - `.gitignore`

### 5. GitHub portfolio and release-readiness work

- Added a public-facing `README.md` in English
- Added `docs/INSTALL_WINDOWS.md` for non-developer Windows installation guidance
- Added `requirements-dev.txt`
- Added `BRender.spec`
- Added `scripts/build_windows.ps1`
- Added `scripts/package_release.ps1`

### 6. Release and installation flow was reviewed and hardened

- Identified and fixed that `BRender.spec` was being ignored by `.gitignore`
- Aligned documentation with the actual versioned release zip naming:
  - `BRender-Windows-<version>.zip`
- Updated build/install docs to avoid reliance on `Activate.ps1`
- Updated `scripts/build_windows.ps1` to use `.\.venv\Scripts\python.exe`
- Updated release packaging to include:
  - `BRender.exe`
  - `README.md`
  - `INSTALL_WINDOWS.md`
- Removed placeholder package URLs from `pyproject.toml`

### 7. Git context confirmed during documentation pass

- Repository was clean at time of continuity-document creation
- Confirmed visible Git history:
  - `013ebb6` - `first commit`
  - `6a58814` - `github optmization one`
  - `7b4c319` - `Windows easy install`
  - `c1b53df` - `Review on files and executable`
- Confirmed `HEAD` was on `main` and tagged `v0.1.0` at the time of inspection

## Not confirmed during this conversation

- Successful generation of `dist/BRender.exe`
- Successful generation of `dist/BRender-Windows-0.1.0.zip`
- Real public GitHub repository URL
- Existence of a public license file
