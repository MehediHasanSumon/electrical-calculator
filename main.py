"""Entry point and application controller for Electrical Calculator."""

from collections.abc import Callable
import sys

from rich.console import Console

from calculator import CalculationResult, ElectricalCalculator
from constants import AppAction, MenuSignal, OhmsLawAction, OHM_SYMBOL
from menu import ArrowMenu, MenuOption, create_key_reader
from ui import ApplicationExit, NavigationBack, TerminalUI
from utils import InputValidationError, parse_number, parse_number_list


class ElectricalCalculatorApp:
    """Coordinate menus, validated input, calculations, and output."""

    def __init__(self) -> None:
        self.console = Console(highlight=False)
        self.key_reader = create_key_reader()
        self.ui = TerminalUI(self.console, self.key_reader)
        self.calculator = ElectricalCalculator()

    def run(self) -> int:
        """Run continuously until the user explicitly exits."""

        self.ui.set_window_title()
        try:
            while True:
                action = self._main_menu()
                if action in (AppAction.EXIT, MenuSignal.QUIT):
                    break
                self._dispatch_main_action(action)
        except (ApplicationExit, KeyboardInterrupt, EOFError):
            pass
        finally:
            self.ui.show_goodbye()
        return 0

    def _main_menu(self) -> AppAction | MenuSignal:
        menu = ArrowMenu(
            self.console,
            self.key_reader,
            "MAIN MENU",
            (
                MenuOption(
                    "Series Resistance",
                    AppAction.SERIES,
                    description="Req = R₁ + R₂ + ...",
                ),
                MenuOption(
                    "Parallel Resistance",
                    AppAction.PARALLEL,
                    description="1/Req = 1/R₁ + 1/R₂ + ...",
                ),
                MenuOption(
                    "Ohm's Law Suite",
                    AppAction.OHMS_LAW,
                    description="V, I, R & Power equations",
                ),
                MenuOption(
                    "Clear Screen",
                    AppAction.CLEAR,
                    description="Clean terminal workspace",
                ),
                MenuOption(
                    "Help & Formulas",
                    AppAction.HELP,
                    description="Shortcuts & physics guide",
                ),
                MenuOption(
                    "Exit Calculator",
                    AppAction.EXIT,
                    description="Quit the application",
                ),
            ),
            allow_back=False,
        )
        return menu.run(self.ui)

    def _dispatch_main_action(
        self, action: AppAction | MenuSignal
    ) -> None:
        if action is AppAction.SERIES:
            self._run_guarded(self._series_resistance)
        elif action is AppAction.PARALLEL:
            self._run_guarded(self._parallel_resistance)
        elif action is AppAction.OHMS_LAW:
            self._ohms_law_menu()
        elif action is AppAction.CLEAR:
            self.ui.clear()
        elif action is AppAction.HELP:
            self.ui.show_help()

    def _series_resistance(self) -> None:
        resistors = self._read_resistors(
            "SERIES RESISTANCE",
            minimum=0,
            instructions=(
                "Formula: Req = R₁ + R₂ + R₃ + ...",
                f"Enter resistor values in ohms ({OHM_SYMBOL}) separated by commas (e.g. 10, 22.5, 47)",
                "Controls: Enter = Calculate  |  Esc = Back  |  Q = Exit",
            ),
        )
        result = self.calculator.series_resistance(resistors)
        self.ui.show_result(result)

    def _parallel_resistance(self) -> None:
        resistors = self._read_resistors(
            "PARALLEL RESISTANCE",
            minimum=0,
            minimum_inclusive=False,
            instructions=(
                "Formula: 1/Req = 1/R₁ + 1/R₂ + 1/R₃ + ...",
                f"Enter branch values in ohms ({OHM_SYMBOL}) separated by commas (values must be > 0)",
                "Controls: Enter = Calculate  |  Esc = Back  |  Q = Exit",
            ),
        )
        result = self.calculator.parallel_resistance(resistors)
        self.ui.show_result(result)

    def _read_resistors(
        self,
        title: str,
        *,
        minimum: float,
        minimum_inclusive: bool = True,
        instructions: tuple[str, ...],
    ) -> list[float]:
        self.ui.render_input_screen(title, instructions)
        raw_values = self.ui.read_line(
            f"R1, R2, R3... ({OHM_SYMBOL}) = "
        )
        return parse_number_list(
            raw_values,
            field_name="Resistance",
            minimum=minimum,
            minimum_inclusive=minimum_inclusive,
        )

    def _ohms_law_menu(self) -> None:
        menu = ArrowMenu(
            self.console,
            self.key_reader,
            "OHM'S LAW SUITE",
            (
                MenuOption(
                    "Voltage (V)",
                    OhmsLawAction.VOLTAGE,
                    description="Calculate V = I × R",
                ),
                MenuOption(
                    "Current (I)",
                    OhmsLawAction.CURRENT,
                    description="Calculate I = V / R",
                ),
                MenuOption(
                    f"Resistance (R)",
                    OhmsLawAction.RESISTANCE,
                    description="Calculate R = V / I",
                ),
                MenuOption(
                    "Electric Power (P)",
                    OhmsLawAction.POWER,
                    description="Calculate P = V×I | I²R | V²/R",
                ),
            ),
            allow_back=True,
        )

        while True:
            action = menu.run(self.ui)
            if action is MenuSignal.BACK:
                return
            if action is MenuSignal.QUIT:
                raise ApplicationExit

            handlers: dict[OhmsLawAction, Callable[[], None]] = {
                OhmsLawAction.VOLTAGE: self._calculate_voltage,
                OhmsLawAction.CURRENT: self._calculate_current,
                OhmsLawAction.RESISTANCE: self._calculate_resistance,
                OhmsLawAction.POWER: self._calculate_power,
            }
            self._run_guarded(handlers[action])

    def _calculate_voltage(self) -> None:
        self.ui.render_input_screen(
            "CALCULATE VOLTAGE",
            ("Formula: V = I x R", "Esc = Back"),
        )
        current = self._required_number("Current (A) = ", "Current")
        resistance = self._required_number(
            f"Resistance ({OHM_SYMBOL}) = ",
            "Resistance",
            minimum=0,
        )
        self.ui.show_result(self.calculator.voltage(current, resistance))

    def _calculate_current(self) -> None:
        self.ui.render_input_screen(
            "CALCULATE CURRENT",
            ("Formula: I = V / R", "Esc = Back"),
        )
        voltage = self._required_number("Voltage (V) = ", "Voltage")
        resistance = self._required_number(
            f"Resistance ({OHM_SYMBOL}) = ",
            "Resistance",
            minimum=0,
            minimum_inclusive=False,
        )
        self.ui.show_result(self.calculator.current(voltage, resistance))

    def _calculate_resistance(self) -> None:
        self.ui.render_input_screen(
            "CALCULATE RESISTANCE",
            ("Formula: R = V / I", "Esc = Back"),
        )
        voltage = self._required_number("Voltage (V) = ", "Voltage")
        current = self._required_number(
            "Current (A) = ", "Current", nonzero=True
        )
        self.ui.show_result(
            self.calculator.resistance(voltage, current)
        )

    def _calculate_power(self) -> None:
        self.ui.render_input_screen(
            "CALCULATE POWER",
            (
                "Enter known values and leave unknown values blank.",
                "Supported: P = V x I, P = I^2 x R, P = V^2 / R",
                "Esc = Back",
            ),
        )
        voltage = self._optional_number("Voltage (V) = ", "Voltage")
        current = self._optional_number("Current (A) = ", "Current")
        resistance = self._optional_number(
            f"Resistance ({OHM_SYMBOL}) = ",
            "Resistance",
            minimum=0,
        )
        result = self.calculator.power(
            voltage=voltage,
            current=current,
            resistance=resistance,
        )
        self.ui.show_result(result)

    def _required_number(
        self,
        prompt: str,
        field_name: str,
        *,
        minimum: float | None = None,
        minimum_inclusive: bool = True,
        nonzero: bool = False,
    ) -> float:
        raw_value = self.ui.read_line(prompt)
        return parse_number(
            raw_value,
            field_name=field_name,
            minimum=minimum,
            minimum_inclusive=minimum_inclusive,
            nonzero=nonzero,
        )

    def _optional_number(
        self,
        prompt: str,
        field_name: str,
        *,
        minimum: float | None = None,
    ) -> float | None:
        raw_value = self.ui.read_line(prompt, allow_blank=True)
        if not raw_value.strip():
            return None
        return parse_number(
            raw_value,
            field_name=field_name,
            minimum=minimum,
        )

    def _run_guarded(self, operation: Callable[[], None]) -> None:
        """Run one operation and return safely after recoverable errors."""

        try:
            operation()
        except NavigationBack:
            return
        except (InputValidationError, ValueError, ZeroDivisionError) as exc:
            self.ui.show_error(str(exc) or "Invalid input.")
        except ApplicationExit:
            raise
        except KeyboardInterrupt as exc:
            raise ApplicationExit from exc
        except Exception:
            self.ui.show_error(
                "The calculation could not be completed. Please try again."
            )


def main() -> int:
    """Create and run the application."""

    _configure_console_encoding()
    try:
        app = ElectricalCalculatorApp()
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return 1
    return app.run()


def _configure_console_encoding() -> None:
    """Use UTF-8 for electrical symbols in legacy Windows terminals."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    raise SystemExit(main())
