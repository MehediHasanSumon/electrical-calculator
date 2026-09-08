"""Rich terminal presentation and editable input controls."""

import sys
from typing import Sequence

from colorama import Fore, Style, just_fix_windows_console
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from calculator import CalculationResult
from constants import (
    APP_NAME,
    APP_VERSION,
    Key,
    OHM_SYMBOL,
    SEPARATOR_WIDTH,
    Styles,
)
from menu import ArrowMenu, KeyPress, KeyReader, MenuOption, WindowsKeyReader


class NavigationBack(Exception):
    """Raised when Escape requests a return to the previous screen."""


class ApplicationExit(Exception):
    """Raised when Q or Ctrl+C requests a graceful application exit."""


class TerminalUI:
    """Owns all terminal drawing, input editing, and user messages."""

    def __init__(
        self,
        console: Console,
        key_reader: KeyReader,
    ) -> None:
        just_fix_windows_console()
        self.console = console
        self.key_reader = key_reader

    def set_window_title(self) -> None:
        """Set the Windows terminal title without invoking a shell."""

        sys.stdout.write(
            f"\x1b]0;{APP_NAME} v{APP_VERSION}\x07"
        )
        sys.stdout.flush()

    def clear(self) -> None:
        """Clear the active terminal screen."""

        self.console.clear()

    def render_menu(
        self,
        title: str,
        options: Sequence[MenuOption[object]],
        selected_index: int,
    ) -> None:
        """Render a complete menu screen."""

        self.clear()
        self._render_header()
        self.console.print(Align.center(Text(title, style=Styles.SUBHEADER)))
        self.console.print()

        menu_group = Group(
            *(
                ArrowMenu.option_text(
                    option.label, index == selected_index
                )
                for index, option in enumerate(options)
            )
        )
        self.console.print(
            Panel(
                menu_group,
                border_style="bright_blue",
                box=box.SQUARE,
                padding=(1, 3),
                width=SEPARATOR_WIDTH,
            )
        )
        self.console.print(
            Align.center(
                Text(
                    "Use Arrow Keys  |  Enter = Select  |  "
                    "Esc = Back  |  Q = Exit",
                    style=Styles.MUTED,
                )
            )
        )

    def render_input_screen(
        self,
        title: str,
        instructions: Sequence[str] = (),
    ) -> None:
        """Render a calculation input screen."""

        self.clear()
        self._render_header()
        self.console.print(Text(title, style=Styles.SUBHEADER))
        self.console.print("-" * SEPARATOR_WIDTH, style="blue")
        for instruction in instructions:
            self.console.print(instruction, style=Styles.MUTED)
        if instructions:
            self.console.print()

    def read_line(
        self,
        prompt: str,
        *,
        allow_blank: bool = False,
    ) -> str:
        """Read an editable line using direct key events.

        Left, right, Home, End, Backspace, and Delete edit the buffer. Escape
        goes back, while Q and Ctrl+C exit the application.
        Tab is consumed so it cannot unexpectedly change terminal focus.
        """

        buffer: list[str] = []
        cursor = 0
        colored_prompt = f"{Fore.CYAN}{prompt}{Style.RESET_ALL}"
        self._redraw_input(colored_prompt, buffer, cursor)

        while True:
            key_press = self.key_reader.read_key()

            if key_press.key is Key.ENTER:
                value = "".join(buffer)
                sys.stdout.write("\n")
                sys.stdout.flush()
                if value.strip() or allow_blank:
                    return value
                return ""

            if key_press.key is Key.ESCAPE:
                sys.stdout.write("\n")
                sys.stdout.flush()
                raise NavigationBack

            if key_press.key is Key.CTRL_C:
                sys.stdout.write("\n")
                sys.stdout.flush()
                raise ApplicationExit

            if (
                key_press.key is Key.CHARACTER
                and key_press.character.casefold() == "q"
            ):
                sys.stdout.write("\n")
                sys.stdout.flush()
                raise ApplicationExit

            buffer, cursor = self._edit_buffer(
                buffer, cursor, key_press
            )
            self._redraw_input(colored_prompt, buffer, cursor)

    def show_result(self, result: CalculationResult) -> None:
        """Render a professional calculation result box."""

        self.clear()
        self._render_header()

        content = Table.grid(padding=(0, 1))
        content.add_column(style="white")
        content.add_row(Text("Calculation Complete", style=Styles.SUCCESS))
        content.add_row(Text(result.title, style=Styles.SUBHEADER))
        content.add_row("")

        for item in result.inputs:
            content.add_row(f"{item.label} = {item.value}")

        content.add_row("")
        content.add_row(Text("Calculation Steps", style="bold yellow"))
        for step in result.steps:
            content.add_row(step)

        content.add_row("")
        content.add_row(Text("-" * 30, style="blue"))
        content.add_row(Text(result.result_label, style="bold white"))
        content.add_row(Text(result.result_value, style=Styles.VALUE))

        self.console.print(
            Panel(
                content,
                border_style="green",
                box=box.DOUBLE,
                padding=(1, 2),
                width=SEPARATOR_WIDTH,
            )
        )
        self.pause()

    def show_error(self, message: str = "Invalid input.") -> None:
        """Display a recoverable error and wait for acknowledgement."""

        self.console.print()
        self.console.print(
            Panel(
                Text(message or "Invalid input.", style=Styles.ERROR),
                title="Invalid Input",
                border_style="red",
                box=box.SQUARE,
                width=SEPARATOR_WIDTH,
            )
        )
        self.pause()

    def show_help(self) -> None:
        """Display keyboard controls and calculation guidance."""

        self.clear()
        self._render_header()
        help_table = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style=Styles.SUBHEADER,
            width=SEPARATOR_WIDTH,
        )
        help_table.add_column("Key", width=16)
        help_table.add_column("Action")
        help_table.add_row("Up / Left", "Move to the previous menu item")
        help_table.add_row("Down / Right / Tab", "Move to the next menu item")
        help_table.add_row("Home / End", "Jump to the first / last item")
        help_table.add_row("Enter", "Select or submit")
        help_table.add_row("Esc", "Return to the previous menu")
        help_table.add_row("Backspace / Delete", "Edit numeric input")
        help_table.add_row("Q", "Exit when a menu or empty prompt is active")
        help_table.add_row("Ctrl+C", "Exit gracefully at any time")

        self.console.print(help_table)
        self.console.print()
        self.console.print(
            "Resistance values cannot be negative. Parallel resistance "
            "values must be greater than zero.",
            style=Styles.WARNING,
        )
        self.console.print(
            "For power, enter any supported pair: V + I, I + R, or V + R. "
            "Leave unknown values blank.",
            style=Styles.MUTED,
        )
        self.pause()

    def show_goodbye(self) -> None:
        """Clear the screen and print the final exit message."""

        self.clear()
        self.console.print(
            Panel(
                Align.center(
                    Text(
                        "Thank you for using Electrical Calculator.",
                        style=Styles.SUCCESS,
                    )
                ),
                border_style="bright_blue",
                box=box.DOUBLE,
                width=SEPARATOR_WIDTH,
            )
        )

    def pause(self, message: str = "Press any key...") -> None:
        """Pause while still honoring global exit controls."""

        self.console.print()
        self.console.print(message, style=Styles.MUTED, end="")
        key_press = self.key_reader.read_key()
        self.console.print()

        if key_press.key is Key.CTRL_C:
            raise ApplicationExit
        if (
            key_press.key is Key.CHARACTER
            and key_press.character.casefold() == "q"
        ):
            raise ApplicationExit

    def _render_header(self) -> None:
        title = Text(f"{APP_NAME} v{APP_VERSION}", style=Styles.HEADER)
        subtitle = Text(
            f"Voltage  |  Current  |  Resistance ({OHM_SYMBOL})  |  Power",
            style=Styles.MUTED,
        )
        self.console.print(
            Panel(
                Align.center(Group(title, subtitle)),
                border_style="bright_blue",
                box=box.DOUBLE,
                width=SEPARATOR_WIDTH,
            )
        )

    @staticmethod
    def _edit_buffer(
        buffer: list[str],
        cursor: int,
        key_press: KeyPress,
    ) -> tuple[list[str], int]:
        """Apply one editing key to an input buffer."""

        if key_press.key is Key.CHARACTER:
            buffer.insert(cursor, key_press.character)
            cursor += 1
        elif key_press.key is Key.BACKSPACE and cursor > 0:
            del buffer[cursor - 1]
            cursor -= 1
        elif key_press.key is Key.DELETE and cursor < len(buffer):
            del buffer[cursor]
        elif key_press.key is Key.LEFT:
            cursor = max(0, cursor - 1)
        elif key_press.key is Key.RIGHT:
            cursor = min(len(buffer), cursor + 1)
        elif key_press.key is Key.HOME:
            cursor = 0
        elif key_press.key is Key.END:
            cursor = len(buffer)
        # Up, Down, and Tab are intentionally consumed in text input.

        return buffer, cursor

    @staticmethod
    def _redraw_input(
        colored_prompt: str,
        buffer: Sequence[str],
        cursor: int,
    ) -> None:
        """Redraw one editable prompt and restore the logical cursor."""

        text = "".join(buffer)
        sys.stdout.write(f"\r\x1b[2K{colored_prompt}{text}")
        characters_after_cursor = len(buffer) - cursor
        if characters_after_cursor:
            sys.stdout.write(f"\x1b[{characters_after_cursor}D")
        sys.stdout.flush()
