# Electrical Calculator

A professional keyboard-driven electrical calculator for Windows CMD and
PowerShell.

## Requirements

- Windows 10 or later
- Python 3.10 or later

## Run

Double-click `run.bat` for automatic environment setup and startup.

To run manually:

```powershell
cd electrical-calculator
python -m pip install -r requirements.txt
python main.py
```

The application uses Windows-native console key reading, so arrow navigation
and line editing do not require administrator privileges or global keyboard
hooks.

## Controls

- Arrow keys: navigate menus
- Enter: select, submit, or calculate
- Escape: return to the previous menu
- Home / End: select the first / last menu item
- Backspace / Delete / Left / Right: edit input
- Q: exit from a menu or input prompt
- Ctrl+C: exit gracefully
