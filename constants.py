"""Application-wide constants and enums."""

from enum import Enum, auto


APP_NAME = "ELECTRICAL CALCULATOR"
APP_VERSION = "1.0"
WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"
SEPARATOR_WIDTH = 54
OHM_SYMBOL = "\u03a9"


class AppAction(Enum):
    """Actions that can be selected from the main menu."""

    SERIES = auto()
    PARALLEL = auto()
    OHMS_LAW = auto()
    CLEAR = auto()
    HELP = auto()
    EXIT = auto()


class OhmsLawAction(Enum):
    """Available Ohm's law calculations."""

    VOLTAGE = auto()
    CURRENT = auto()
    RESISTANCE = auto()
    POWER = auto()


class MenuSignal(Enum):
    """Control signals returned by a menu."""

    BACK = auto()
    QUIT = auto()


class Key(Enum):
    """Normalized terminal keys used throughout the application."""

    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    ENTER = auto()
    ESCAPE = auto()
    BACKSPACE = auto()
    DELETE = auto()
    TAB = auto()
    HOME = auto()
    END = auto()
    CTRL_C = auto()
    CHARACTER = auto()
    UNKNOWN = auto()


class Styles:
    """Rich style names used by the UI."""

    HEADER = "bold bright_blue"
    SUBHEADER = "bold cyan"
    SUCCESS = "bold green"
    WARNING = "bold yellow"
    ERROR = "bold red"
    MUTED = "dim white"
    SELECTED = "bold black on bright_cyan"
    NORMAL = "white"
    VALUE = "bold bright_green"
