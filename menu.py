"""Keyboard handling and reusable arrow-key menus."""

from dataclasses import dataclass
import os
import sys
from typing import Generic, Protocol, Sequence, TypeVar

from rich.console import Console
from rich.text import Text

from constants import Key, MenuSignal, Styles

try:
    import msvcrt
except ImportError:  # pragma: no cover - this application targets Windows
    msvcrt = None  # type: ignore[assignment]

try:
    import select
    import termios
    import tty
except ImportError:  # pragma: no cover - only available on POSIX
    select = None  # type: ignore[assignment]
    termios = None  # type: ignore[assignment]
    tty = None  # type: ignore[assignment]


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


class KeyReader(Protocol):
    """Presentation-neutral keyboard reader contract."""

    def read_key(self) -> KeyPress:
        """Block until one complete key press is available."""


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


class PosixKeyReader:
    """Read individual keys from POSIX (Linux/macOS) terminals."""

    _ESCAPE_MAP = {
        b"\x1b[A": Key.UP,
        b"\x1bOA": Key.UP,
        b"\x1b[B": Key.DOWN,
        b"\x1bOB": Key.DOWN,
        b"\x1b[C": Key.RIGHT,
        b"\x1bOC": Key.RIGHT,
        b"\x1b[D": Key.LEFT,
        b"\x1bOD": Key.LEFT,
        b"\x1b[H": Key.HOME,
        b"\x1bOH": Key.HOME,
        b"\x1b[1~": Key.HOME,
        b"\x1b[7~": Key.HOME,
        b"\x1b[F": Key.END,
        b"\x1bOF": Key.END,
        b"\x1b[4~": Key.END,
        b"\x1b[8~": Key.END,
        b"\x1b[3~": Key.DELETE,
        b"\x1b[Z": Key.TAB,
    }

    _SINGLE_KEY_MAP = {
        b"\r": Key.ENTER,
        b"\n": Key.ENTER,
        b"\x08": Key.BACKSPACE,
        b"\x7f": Key.BACKSPACE,
        b"\t": Key.TAB,
        b"\x03": Key.CTRL_C,
    }

    def __init__(self) -> None:
        if os.name != "posix" or termios is None or tty is None or select is None:
            raise RuntimeError("This reader requires a POSIX terminal.")

    def read_key(self) -> KeyPress:
        """Block until one complete key press is available."""

        fd = sys.stdin.fileno()
        is_tty = sys.stdin.isatty()
        old_settings = None

        if is_tty:
            old_settings = termios.tcgetattr(fd)
            tty.setraw(fd, termios.TCSANOW)

        try:
            raw = os.read(fd, 1)
            if not raw:
                return KeyPress(Key.CTRL_C)

            if raw == b"\x1b":
                seq = b""
                while True:
                    rlist, _, _ = select.select([fd], [], [], 0.05)
                    if not rlist:
                        break
                    chunk = os.read(fd, 32)
                    if not chunk:
                        break
                    seq += chunk
                    if seq.startswith((b"[", b"O")):
                        if len(seq) >= 2 and (0x40 <= seq[-1] <= 0x7E):
                            break
                    else:
                        break

                if not seq:
                    return KeyPress(Key.ESCAPE)

                full_seq = raw + seq
                if full_seq in self._ESCAPE_MAP:
                    return KeyPress(self._ESCAPE_MAP[full_seq])

                if full_seq.startswith(b"\x1b[") and full_seq.endswith(b"A"):
                    return KeyPress(Key.UP)
                if full_seq.startswith(b"\x1b[") and full_seq.endswith(b"B"):
                    return KeyPress(Key.DOWN)
                if full_seq.startswith(b"\x1b[") and full_seq.endswith(b"C"):
                    return KeyPress(Key.RIGHT)
                if full_seq.startswith(b"\x1b[") and full_seq.endswith(b"D"):
                    return KeyPress(Key.LEFT)

                return KeyPress(Key.UNKNOWN)

            if raw in self._SINGLE_KEY_MAP:
                return KeyPress(self._SINGLE_KEY_MAP[raw])

            first_byte = raw[0]
            extra_len = 0
            if (first_byte & 0xE0) == 0xC0:
                extra_len = 1
            elif (first_byte & 0xF0) == 0xE0:
                extra_len = 2
            elif (first_byte & 0xF8) == 0xF0:
                extra_len = 3

            if extra_len > 0:
                extra_bytes = os.read(fd, extra_len)
                raw += extra_bytes

            try:
                char = raw.decode("utf-8")
                if char.isprintable():
                    return KeyPress(Key.CHARACTER, char)
            except UnicodeDecodeError:
                pass

            return KeyPress(Key.UNKNOWN)
        finally:
            if is_tty and old_settings is not None:
                termios.tcsetattr(fd, termios.TCSANOW, old_settings)


def create_key_reader() -> KeyReader:
    """Create a platform-appropriate keyboard reader."""

    if os.name == "nt":
        return WindowsKeyReader()
    if os.name == "posix":
        return PosixKeyReader()
    raise RuntimeError(f"Unsupported operating system: {os.name}")


class ArrowMenu(Generic[T]):
    """Render and operate a keyboard-driven terminal menu."""

    def __init__(
        self,
        console: Console,
        key_reader: KeyReader,
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
