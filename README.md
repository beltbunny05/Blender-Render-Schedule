# BRender

**BRender** is a desktop render queue for Blender artists who want a cleaner way to batch `.blend` files, schedule renders, and monitor long-running jobs from one place.

It is built with Python + CustomTkinter and designed for solo artists, freelancers, and small studios who want a practical queue manager without opening Blender project by project.

## For Blender users who just want to install it

The recommended path is a **prebuilt Windows release**:

1. Go to the repository's **Releases** page
2. Download the latest `BRender-Windows.zip`
3. Extract it
4. Launch `BRender.exe`

That flow is aimed at **non-developers** and does not require Python or terminal setup.

Detailed guide: [`docs/INSTALL_WINDOWS.md`](docs/INSTALL_WINDOWS.md)

## Why this project stands out

- Schedule renders for later and let your machine work overnight
- Batch multiple `.blend` files in one queue
- Optionally render every scene inside each `.blend`
- Open the current queued file location directly from the app
- Monitor output in an integrated terminal log
- Stop renders safely and optionally trigger shutdown when everything is done
- UI designed to feel more modern than a typical utility script

## Preview

This repository currently includes the app source and launcher. If you want to showcase screenshots on GitHub later, add them to a `docs/` or `assets/` folder and link them here.

## Project structure

```text
.
|-- brender/
|   |-- __init__.py
|   |-- __main__.py
|   |-- app.py
|   |-- config.py
|   |-- helpers.py
|   `-- rendering.py
|-- docs/
|   `-- INSTALL_WINDOWS.md
|-- scripts/
|   |-- build_windows.ps1
|   `-- package_release.ps1
|-- BRender.spec
|-- BRender_App.py
|-- blender.ico
|-- pyproject.toml
|-- README.md
|-- requirements-dev.txt
`-- requirements.txt
```

## What each module does

- `brender/app.py`: main desktop app, UI composition, queue interactions, render orchestration
- `brender/config.py`: theme constants, window settings, default paths
- `brender/helpers.py`: platform helpers, font selection, path cleanup, time normalization
- `brender/rendering.py`: Blender subprocess helpers for reading scenes and discovering output paths
- `BRender_App.py`: thin compatibility launcher for users who want to run the app directly

## Installation

### Option A: easiest for artists

Download the latest prebuilt release from the repository's **Releases** page and run `BRender.exe`.

### Option B: run from source

### 1. Clone the repository

```bash
git clone https://github.com/your-username/brender.git
cd brender
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate it

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Run the app

You can start BRender in either of these ways:

```bash
python BRender_App.py
```

or

```bash
python -m brender
```

After installing as a package, you can also use:

```bash
brender
```

## Workflow

1. Choose your Blender executable
2. Add `.blend` files or a whole folder
3. Optionally set a start time
4. Choose whether to render the active scene only or all scenes
5. Start immediately or schedule for later
6. Follow the log output while Blender processes the queue

## Ideal users

- Blender freelancers batching client renders
- Motion designers rendering scene variations overnight
- Small teams who want a lightweight queue tool without a full render farm
- Artists who want a polished desktop helper for local render automation

## Roadmap ideas

- Drag and drop support
- Reordering items inside the queue
- Per-file scene selection
- Saved queue presets
- Exportable render logs
- Signed packaged executable releases
- Thumbnail preview for queued `.blend` files

## Build a Windows executable

If you want to publish a non-developer-friendly build yourself:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
.\scripts\build_windows.ps1
```

The executable will be generated at:

```text
dist/BRender.exe
```

To create a release zip for GitHub Releases:

```powershell
.\scripts\package_release.ps1 -Version 0.1.0
```

## Notes

- The current implementation is primarily tailored for Windows workflows
- Automatic shutdown is only configured for Windows in this version
- The default Blender path may need to be updated for your local install

## Contributing

If you are a Blender user and want to improve the workflow, UI, or packaging, contributions and ideas are welcome.
