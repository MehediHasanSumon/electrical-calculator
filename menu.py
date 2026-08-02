"""Keyboard handling and reusable arrow-key menus."""

from dataclasses import dataclass
import os
from typing import Generic, Protocol, Sequence, TypeVar

from rich.console import Console
from rich.text import Text

from constants import Key, MenuSignal, Styles

try:
    import msvcrt
except ImportError:  # pragma: no cover - this application targets Windows
    msvcrt = None  # type: ignore[assignment]


T = TypeVar("T")


class MenuRenderer(Protocol):
    """Presentation contract required by ArrowMenu."""

    def render_menu(
        self,
        title: str,
        options: Sequence["MenuOption[object]"],
        selected_index: int,
    ) -> None:
        """Render one menu frame."""


@dataclass(frozen=True)
class KeyPress:
    """A normalized key event."""

    key: Key
    character: str = ""


@dataclass(frozen=True)
class MenuOption(Generic[T]):
    """A visible menu label and the value it represents."""

    label: str
    value: T


class WindowsKeyReader:
    """Read individual keys from Windows CMD or PowerShell."""

    _SPECIAL_KEYS = {
        "H": Key.UP,
        "P": Key.DOWN,
        "K": Key.LEFT,
        "M": Key.RIGHT,
        "G": Key.HOME,
        "O": Key.END,
        "S": Key.DELETE,
    }

    def __init__(self) -> None:
        if os.name != "nt" or msvcrt is None:
            raise RuntimeError("This application requires a Windows terminal.")

    def read_key(self) -> KeyPress:
        """Block until one complete key press is available."""

        character = msvcrt.getwch()

        if character in ("\x00", "\xe0"):
            special_character = msvcrt.getwch()
            return KeyPress(
                self._SPECIAL_KEYS.get(special_character, Key.UNKNOWN)
            )

        key_map = {
            "\r": Key.ENTER,
            "\n": Key.ENTER,
            "\x1b": Key.ESCAPE,
            "\x08": Key.BACKSPACE,
            "\t": Key.TAB,
            "\x03": Key.CTRL_C,
            "\x7f": Key.DELETE,
        }
        if character in key_map:
            return KeyPress(key_map[character])
        if character.isprintable():
            return KeyPress(Key.CHARACTER, character)
        return KeyPress(Key.UNKNOWN)

class ArrowMenu(Generic[T]):
    """Render and operate a keyboard-driven terminal menu."""

    def __init__(
        self,
        console: Console,
        key_reader: WindowsKeyReader,
        title: str,
        options: Sequence[MenuOption[T]],
        *,
        allow_back: bool = True,
        start_index: int = 0,
    ) -> None:
        if not options:
            raise ValueError("A menu requires at least one option.")

        self.console = console
        self.key_reader = key_reader
        self.title = title
        self.options = tuple(options)
        self.allow_back = allow_back
        self.selected_index = max(0, min(start_index, len(options) - 1))

    def run(self, renderer: MenuRenderer) -> T | MenuSignal:
        """Display the menu until the user selects an option or leaves."""

        while True:
            renderer.render_menu(self.title, self.options, self.selected_index)
            key_press = self.key_reader.read_key()

            if key_press.key in (Key.UP, Key.LEFT):
                self.selected_index = (
                    self.selected_index - 1
                ) % len(self.options)
            elif key_press.key in (Key.DOWN, Key.RIGHT, Key.TAB):
                self.selected_index = (
                    self.selected_index + 1
                ) % len(self.options)
            elif key_press.key is Key.HOME:
                self.selected_index = 0
            elif key_press.key is Key.END:
                self.selected_index = len(self.options) - 1
            elif key_press.key is Key.ENTER:
                return self.options[self.selected_index].value
            elif key_press.key is Key.ESCAPE and self.allow_back:
                return MenuSignal.BACK
            elif key_press.key is Key.CTRL_C:
                return MenuSignal.QUIT
            elif (
                key_press.key is Key.CHARACTER
                and key_press.character.casefold() == "q"
            ):
                return MenuSignal.QUIT

    @staticmethod
    def option_text(label: str, selected: bool) -> Text:
        """Build consistently styled text for a menu option."""

        prefix = "\u25ba " if selected else "  "
        text = Text(f"{prefix}{label}")
        text.stylize(Styles.SELECTED if selected else Styles.NORMAL)
        return text
