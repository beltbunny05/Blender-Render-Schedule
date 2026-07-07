# DECISIONS.md

## 1. The project was modularized out of the original monolith

### Decision

Move from a single large `BRender_App.py` implementation to a package-based structure under `brender/`, while keeping `BRender_App.py` as a thin launcher.

### Why

- Better portfolio presentation
- Easier maintenance
- Clear separation between UI, configuration, helpers, and Blender subprocess logic

### Alternatives considered or implicitly discarded

- Keep everything in one file
- Split only partially while leaving most logic in the root script

### Consequences

- More maintainable codebase
- Slightly more files to keep in sync
- Public entry point remains simple for end users

### Affected files

- `BRender_App.py`
- `brender/__init__.py`
- `brender/__main__.py`
- `brender/app.py`
- `brender/config.py`
- `brender/helpers.py`
- `brender/rendering.py`

## 2. The UI was reorganized into workflow-based sections

### Decision

Group actions into:

- Build queue
- Start render
- Control and power

### Why

- Cleaner UX
- Lower cognitive load
- More natural task flow for Blender users

### Alternatives considered or implicitly discarded

- Keep all actions in a flat toolbar/button strip

### Consequences

- UI became clearer and more portfolio-friendly
- Action hierarchy is now part of the product identity and should be preserved unless there is a better replacement

### Affected files

- `brender/app.py`

## 3. The "open location" action now opens the current queued file folder

### Decision

Change the previous render-location behavior so the UI button opens the folder of the current `.blend` file in the queue.

### Why

- Requested directly by the user
- More useful during queue preparation
- Avoids relying on discovering Blender output paths for this specific button

### Alternatives discarded

- Keep opening the current render output location
- Resolve and open output paths asynchronously from Blender for the same button

### Consequences

- The render-output discovery helper still exists in the codebase, but the main UI action no longer uses it
- Future changes should not silently revert this behavior

### Affected files

- previously monolithic `BRender_App.py`
- current `brender/app.py`
- `brender/rendering.py` still contains output-path helper logic

## 4. The UI and documentation were standardized to English

### Decision

Convert UI text, user-facing messages, and public documentation to English.

### Why

- Requested directly by the user
- Better fit for a public GitHub portfolio and broader Blender audience

### Alternatives discarded

- Keep Portuguese UI
- Maintain mixed-language UI/docs

### Consequences

- New work should preserve English consistency unless explicit localization is requested

### Affected files

- `brender/app.py`
- `README.md`
- `docs/INSTALL_WINDOWS.md`

## 5. Windows packaging was prioritized for non-developer installation

### Decision

Add PyInstaller-based packaging and a release zip flow aimed at users who do not want to install Python.

### Why

- The user explicitly wanted an easier installation process for non-developers
- Blender users often prefer a download-and-run flow

### Alternatives discarded

- Source-only distribution
- Requiring Python and terminal commands for all users

### Consequences

- Build/release tooling is now part of the project surface
- The repo must preserve `BRender.spec`, build scripts, and installation docs

### Affected files

- `BRender.spec`
- `scripts/build_windows.ps1`
- `scripts/package_release.ps1`
- `requirements-dev.txt`
- `README.md`
- `docs/INSTALL_WINDOWS.md`

## 6. Build scripts must not rely on PowerShell activation

### Decision

Use `.\.venv\Scripts\python.exe` directly in scripts and docs instead of depending on `Activate.ps1`.

### Why

- During this conversation, PowerShell execution policy blocked `Activate.ps1`
- Direct interpreter usage is more reliable and reproducible

### Alternatives discarded

- Continue documenting `.venv\Scripts\Activate.ps1` as the default flow
- Use the global `python` command in build scripts

### Consequences

- The docs and scripts are more Windows-robust
- Future updates should not reintroduce activation-only guidance

### Affected files

- `scripts/build_windows.ps1`
- `README.md`
- `docs/INSTALL_WINDOWS.md`

## 7. Release artifact naming is versioned

### Decision

The packaged release artifact should be named `BRender-Windows-<version>.zip`.

### Why

- Better GitHub Releases organization
- Avoid ambiguity between versions

### Alternatives discarded

- Generic `BRender-Windows.zip`

### Consequences

- Docs and release notes must reference the versioned filename
- Build/release instructions must stay consistent with the script output

### Affected files

- `scripts/package_release.ps1`
- `README.md`
- `docs/INSTALL_WINDOWS.md`

## 8. Placeholder GitHub metadata should not be published

### Decision

Remove placeholder `your-username` URLs from package metadata instead of shipping knowingly incorrect links.

### Why

- Placeholder URLs reduce credibility
- Unknown real repo URL was not confirmed at the time

### Alternatives discarded

- Keep fake/placeholder URLs in `pyproject.toml`

### Consequences

- Public metadata remains incomplete until the real repository URL is known
- README still needs a real clone URL update before public launch

### Affected files

- `pyproject.toml`
- `README.md`
