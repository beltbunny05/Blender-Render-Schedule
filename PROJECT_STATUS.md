# PROJECT_STATUS.md

## Overall objective

Deliver BRender as a polished, portfolio-ready, Windows-first Blender render queue application with a cleaner UI, modular Python codebase, and a non-developer-friendly release flow based on a packaged executable and GitHub Releases.

## Current repository state

- Git status: clean at time of documentation update
- Current branch: `main`
- Current HEAD: `c1b53df`
- Current tag at HEAD: `v0.1.0`
- Existing top-level deliverables:
  - modular Python package under `brender/`
  - launcher `BRender_App.py`
  - PyInstaller spec `BRender.spec`
  - build/package PowerShell scripts
  - English README and Windows install guide

## Completed functionality

- Modern CustomTkinter desktop UI
- English-language interface
- Queue multiple `.blend` files
- Queue `.blend1` files discovered in folder import
- Add files individually
- Add a folder of files
- Scheduled render start time
- Immediate render option
- Optional render-all-scenes mode using Blender scene discovery
- Integrated terminal/log panel
- Stop render flow
- Open the current queued file location
- Optional Windows shutdown after all renders finish
- Modularized codebase (`brender/app.py`, `config.py`, `helpers.py`, `rendering.py`)
- Windows build script and release packaging script
- README and non-developer installation documentation

## Partially completed or not fully confirmed

- Windows executable build flow exists, but successful build is **not confirmed in this conversation**
- Release zip packaging flow exists, but generated artifact is **not confirmed in this conversation**
- Public GitHub metadata is partially prepared, but the real repository URL is still **not confirmed**
- GitHub Release page content was drafted in conversation, but actual release publication is **not confirmed**

## Known issues / risks

- `README.md` still contains a placeholder clone URL: `https://github.com/your-username/brender.git`
- No `LICENSE` file exists yet
- No `CHANGELOG.md` for public releases exists yet
- No screenshots/GIFs are included for portfolio presentation
- No automated tests exist
- No committed proof of a successful `dist/BRender.exe` build exists in the repository
- `brender/rendering.py` contains `get_render_output_folder_from_blender`, but that helper is not currently used by `brender/app.py`

## Important product decisions already reflected in the code

- UI should stay in English
- The queue-location action should open the folder of the current `.blend` file, not the render output location
- Build instructions should avoid PowerShell activation dependency and use `.\.venv\Scripts\python.exe` directly
- Release artifact naming is versioned: `BRender-Windows-<version>.zip`
- The project should remain modular and not return to the previous monolith structure

## Most important files

- `brender/app.py`
- `brender/rendering.py`
- `brender/helpers.py`
- `brender/config.py`
- `BRender_App.py`
- `BRender.spec`
- `scripts/build_windows.ps1`
- `scripts/package_release.ps1`
- `README.md`
- `docs/INSTALL_WINDOWS.md`

## Recommended next steps

1. Replace the placeholder repository URL in `README.md` with the real GitHub URL.
2. Decide and add a license file.
3. Run and verify the Windows build:
   - `.\scripts\build_windows.ps1`
   - `.\scripts\package_release.ps1 -Version 0.1.0`
4. Confirm the release zip contents and actual runtime of `BRender.exe`.
5. Add screenshots or a GIF to `README.md`.
6. Optionally add a public `CHANGELOG.md` separate from `CHANGELOG_DEV.md`.
7. Decide whether to remove or integrate the currently unused `get_render_output_folder_from_blender` helper.

## How to resume work safely

1. Read `AGENTS.md` first.
2. Read `DECISIONS.md` for the reasoning behind the current structure and release flow.
3. Read `CHANGELOG_DEV.md` for the chronology of what was changed during this Codex session.
4. Confirm the real GitHub repo URL and intended license before modifying public-facing files.
5. If continuing on build/release topics, validate on Windows with the `.venv` Python path instead of relying on `Activate.ps1`.

## Not confirmed

- Whether `dist/BRender.exe` currently builds successfully on the user machine after the latest repository changes
- Whether `dist/BRender-Windows-0.1.0.zip` has already been generated
- Whether a public GitHub repository URL already exists
