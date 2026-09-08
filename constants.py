"""Application-wide constants and enums."""

from enum import Enum, auto


APP_NAME = "ELECTRICAL CALCULATOR"
APP_VERSION = "1.0"
WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"
SEPARATOR_WIDTH = 68
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

    HEADER = "bold bright_cyan"
    SUBHEADER = "bold bright_yellow"
    ACCENT = "bold cyan"
    SUCCESS = "bold bright_green"
    WARNING = "bold yellow"
    ERROR = "bold bright_red"
    MUTED = "dim white"
    SELECTED = "bold black on bright_cyan"
    SELECTED_DESC = "italic cyan on black"
    NORMAL = "bright_white"
    NORMAL_DESC = "dim white"
    VALUE = "bold bright_green"
    BORDER = "bright_blue"
    FORMULA = "italic bright_cyan"
    PROMPT = "bold bright_cyan"
