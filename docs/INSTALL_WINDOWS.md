# Install BRender on Windows

## Recommended for most Blender users

Use the **prebuilt release**.

1. Open the repository's **Releases** page
2. Download the latest `BRender-Windows.zip`
3. Extract the zip anywhere you want
4. Double-click `BRender.exe`

This is the easiest option because it does **not** require Python, Git, or terminal commands.

## If Windows shows a security warning

Because BRender may be distributed as an unsigned executable:

1. Click `More info`
2. Click `Run anyway`

Only do this if you trust the release source.

## If you want to run from source

Use this only if you are comfortable with Python:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python BRender_App.py
```

## Blender setup

Inside BRender:

1. Point the app to your `blender.exe`
2. Add one or more `.blend` files
3. Choose whether to render now or at a scheduled time
4. Optionally enable all scenes or shutdown after finish
