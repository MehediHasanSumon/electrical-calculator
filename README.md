# Electrical Calculator

A professional keyboard-driven electrical calculator for Linux and Windows
terminals.

## Requirements

- Linux (Ubuntu, Debian, Fedora, Arch, etc.) or Windows 10/11
- Python 3.10 or later

## Run

### Linux

Run the launcher script for automatic environment setup and startup:

```bash
./run.sh
```

Or run manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### Windows

Double-click `run.bat` for automatic environment setup and startup.

Or run manually in PowerShell / Command Prompt:

```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

The application uses native console key reading (POSIX termios on Linux,
msvcrt on Windows), so arrow navigation and line editing do not require
administrator privileges or external window systems.

## Controls

- Arrow keys: navigate menus
- Enter: select, submit, or calculate
- Escape: return to the previous menu
- Home / End: select the first / last menu item
- Backspace / Delete / Left / Right: edit input
- Q: exit from a menu or input prompt
- Ctrl+C: exit gracefully
