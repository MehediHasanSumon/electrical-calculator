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
        self.console.print(Align.center(Text(f"── {title} ──", style=Styles.SUBHEADER)))
        self.console.print()

        menu_group = Group(
            *(
                ArrowMenu.option_text(
                    option, index == selected_index
                )
                for index, option in enumerate(options)
            )
        )
        self.console.print(
            Panel(
                menu_group,
                border_style=Styles.BORDER,
                box=box.ROUNDED,
                padding=(1, 2),
                width=SEPARATOR_WIDTH,
            )
        )
        self.console.print()

        footer = Text()
        footer.append(" [", style="dim")
        footer.append(" ↑/↓ ", style="bold black on bright_white")
        footer.append("] Move   [", style="dim")
        footer.append(" Enter ", style="bold black on bright_cyan")
        footer.append("] Select   [", style="dim")
        footer.append(" Esc ", style="bold black on bright_yellow")
        footer.append("] Back   [", style="dim")
        footer.append(" Q ", style="bold black on bright_red")
        footer.append("] Exit", style="dim")
        self.console.print(Align.center(footer))

    def render_input_screen(
        self,
        title: str,
        instructions: Sequence[str] = (),
    ) -> None:
        """Render a calculation input screen."""

        self.clear()
        self._render_header()

        instr_items: list[Text] = [
            Text(title, style=Styles.SUBHEADER),
            Text("─" * (SEPARATOR_WIDTH - 6), style="dim cyan"),
        ]
        for instruction in instructions:
            instr_items.append(Text(f" • {instruction}", style=Styles.MUTED))

        self.console.print(
            Panel(
                Group(*instr_items),
                border_style=Styles.BORDER,
                box=box.ROUNDED,
                padding=(1, 2),
                width=SEPARATOR_WIDTH,
            )
        )
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
        colored_prompt = f"  {Fore.CYAN}> {prompt}{Style.RESET_ALL}"
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
        content.add_row(Text(result.title, style=Styles.SUCCESS))
        content.add_row(Text("─" * (SEPARATOR_WIDTH - 6), style="dim green"))
        content.add_row("")

        content.add_row(Text("INPUT PARAMETERS:", style=Styles.ACCENT))
        for item in result.inputs:
            content.add_row(Text(f"  • {item.label:<16} = {item.value}", style="bright_white"))
        content.add_row("")

        content.add_row(Text("CALCULATION STEPS:", style=Styles.SUBHEADER))
        for step in result.steps:
            content.add_row(Text(f"  > {step}", style="yellow"))
        content.add_row("")

        content.add_row(Text("═" * (SEPARATOR_WIDTH - 6), style="dim green"))
        res_badge = Text()
        res_badge.append(f" {result.result_label}: ", style="bold bright_white")
        res_badge.append(f" {result.result_value} ", style="bold black on bright_green")
        content.add_row(Align.center(res_badge))
        content.add_row(Text("═" * (SEPARATOR_WIDTH - 6), style="dim green"))

        self.console.print(
            Panel(
                content,
                border_style="bright_green",
                box=box.ROUNDED,
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
                title="[bold bright_red] Input Error [/]",
                border_style="bright_red",
                box=box.ROUNDED,
                padding=(0, 2),
                width=SEPARATOR_WIDTH,
            )
        )
        self.pause()

    def show_help(self) -> None:
        """Display keyboard controls and calculation guidance."""

        self.clear()
        self._render_header()
        help_table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold bright_cyan",
            border_style=Styles.BORDER,
            width=SEPARATOR_WIDTH,
        )
        help_table.add_column("Key Shortcut", style="bold bright_white", width=22)
        help_table.add_column("Action", style="white")
        help_table.add_row("↑ / ↓ / Tab", "Navigate menu options")
        help_table.add_row("Home / End", "Jump to first / last item")
        help_table.add_row("Enter", "Select option / Calculate")
        help_table.add_row("Esc", "Return to previous screen")
        help_table.add_row("Backspace / Delete", "Edit text & numeric values")
        help_table.add_row("Q", "Exit active menu / screen")
        help_table.add_row("Ctrl+C", "Exit application gracefully")

        self.console.print(help_table)
        self.console.print()

        formula_table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold bright_yellow",
            border_style="yellow",
            width=SEPARATOR_WIDTH,
        )
        formula_table.add_column("Circuit / Law", style="bold bright_white", width=22)
        formula_table.add_column("Formula Reference", style="bright_cyan")
        formula_table.add_row("Series Resistance", f"Req = R₁ + R₂ + R₃ + ... ({OHM_SYMBOL})")
        formula_table.add_row("Parallel Resistance", f"1/Req = 1/R₁ + 1/R₂ + ... ({OHM_SYMBOL})")
        formula_table.add_row("Ohm's Law (V)", "V = I × R  (Voltage)")
        formula_table.add_row("Ohm's Law (I)", "I = V / R  (Current)")
        formula_table.add_row("Ohm's Law (R)", f"R = V / I  (Resistance in {OHM_SYMBOL})")
        formula_table.add_row("Electric Power (P)", "P = V × I  |  P = I² × R  |  P = V² / R")

        self.console.print(formula_table)
        self.pause()

    def show_goodbye(self) -> None:
        """Clear the screen and print the final exit message."""

        self.clear()
        goodbye_text = Text()
        goodbye_text.append("Thank you for using Electrical Calculator!\n", style="bold bright_green")
        goodbye_text.append("Have a great day analyzing circuits.", style="dim white")
        self.console.print(
            Panel(
                Align.center(goodbye_text),
                border_style=Styles.BORDER,
                box=box.ROUNDED,
                padding=(1, 2),
                width=SEPARATOR_WIDTH,
            )
        )

    def pause(self, message: str = "Press any key to continue...") -> None:
        """Pause while still honoring global exit controls."""

        self.console.print()
        prompt_text = Text()
        prompt_text.append(" [", style="dim")
        prompt_text.append(" Press Any Key ", style="bold black on bright_white")
        prompt_text.append("] to continue... (or ", style="dim")
        prompt_text.append("Q", style="bold bright_red")
        prompt_text.append(" to exit)", style="dim")
        self.console.print(Align.center(prompt_text))
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
        title = Text()
        title.append(APP_NAME, style=Styles.HEADER)
        title.append(f" v{APP_VERSION}", style=Styles.SUBHEADER)

        subtitle = Text(
            f"Voltage (V)  •  Current (I)  •  Resistance ({OHM_SYMBOL})  •  Power (P)",
            style=Styles.MUTED,
        )
        self.console.print(
            Panel(
                Align.center(Group(title, subtitle)),
                border_style=Styles.BORDER,
                box=box.ROUNDED,
                padding=(0, 2),
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
