"""Pure electrical calculation services."""

from dataclasses import dataclass
from typing import Sequence

from constants import OHM_SYMBOL
from utils import InputValidationError, format_number, format_step_number


@dataclass(frozen=True)
class DisplayValue:
    """A labeled value displayed in a calculation result."""

    label: str
    value: str


@dataclass(frozen=True)
class CalculationResult:
    """Complete presentation-neutral output from a calculation."""

    title: str
    inputs: tuple[DisplayValue, ...]
    steps: tuple[str, ...]
    result_label: str
    result_value: str


class ElectricalCalculator:
    """Performs electrical calculations and prepares calculation steps."""

    @staticmethod
    def series_resistance(resistors: Sequence[float]) -> CalculationResult:
        """Calculate equivalent resistance for resistors in series."""

        ElectricalCalculator._require_resistors(resistors)
        if any(resistance < 0 for resistance in resistors):
            raise InputValidationError("Resistance cannot be negative.")

        equivalent = sum(resistors)
        values = tuple(
            DisplayValue(f"R{index}", f"{format_number(value)} {OHM_SYMBOL}")
            for index, value in enumerate(resistors, start=1)
        )
        expression = " + ".join(format_number(value) for value in resistors)

        return CalculationResult(
            title="Series Resistance",
            inputs=values,
            steps=(
                f"Req = {expression}",
                f"Req = {format_number(equivalent)} {OHM_SYMBOL}",
            ),
            result_label="Equivalent Resistance",
            result_value=f"{format_number(equivalent)} {OHM_SYMBOL}",
        )

    @staticmethod
    def parallel_resistance(resistors: Sequence[float]) -> CalculationResult:
        """Calculate equivalent resistance for resistors in parallel."""

        ElectricalCalculator._require_resistors(resistors)
        if any(resistance <= 0 for resistance in resistors):
            raise InputValidationError(
                "Parallel resistance values must be greater than zero."
            )

        reciprocal_sum = sum(1.0 / resistance for resistance in resistors)
        equivalent = 1.0 / reciprocal_sum
        values = tuple(
            DisplayValue(f"R{index}", f"{format_number(value)} {OHM_SYMBOL}")
            for index, value in enumerate(resistors, start=1)
        )
        reciprocal_expression = " + ".join(
            f"1/{format_number(value)}" for value in resistors
        )

        return CalculationResult(
            title="Parallel Resistance",
            inputs=values,
            steps=(
                "1 / Req =",
                reciprocal_expression,
                f"1 / Req = {format_step_number(reciprocal_sum)}",
                f"Req = 1 / {format_step_number(reciprocal_sum)}",
                f"Req = {format_number(equivalent)} {OHM_SYMBOL}",
            ),
            result_label="Equivalent Resistance",
            result_value=f"{format_number(equivalent)} {OHM_SYMBOL}",
        )

    @staticmethod
    def voltage(current: float, resistance: float) -> CalculationResult:
        """Calculate voltage using V = I x R."""

        ElectricalCalculator._require_nonnegative_resistance(resistance)
        voltage = current * resistance

        return CalculationResult(
            title="Calculate Voltage",
            inputs=(
                DisplayValue("Current (I)", f"{format_number(current)} A"),
                DisplayValue(
                    "Resistance (R)", f"{format_number(resistance)} {OHM_SYMBOL}"
                ),
            ),
            steps=(
                "V = I x R",
                (
                    f"V = {format_number(current)} x "
                    f"{format_number(resistance)}"
                ),
                f"V = {format_number(voltage)} V",
            ),
            result_label="Voltage",
            result_value=f"{format_number(voltage)} Volt",
        )

    @staticmethod
    def current(voltage: float, resistance: float) -> CalculationResult:
        """Calculate current using I = V / R."""

        if resistance <= 0:
            raise InputValidationError("Resistance must be greater than zero.")

        current = voltage / resistance
        return CalculationResult(
            title="Calculate Current",
            inputs=(
                DisplayValue("Voltage (V)", f"{format_number(voltage)} V"),
                DisplayValue(
                    "Resistance (R)", f"{format_number(resistance)} {OHM_SYMBOL}"
                ),
            ),
            steps=(
                "I = V / R",
                (
                    f"I = {format_number(voltage)} / "
                    f"{format_number(resistance)}"
                ),
                f"I = {format_number(current)} A",
            ),
            result_label="Current",
            result_value=f"{format_number(current)} Ampere",
        )

    @staticmethod
    def resistance(voltage: float, current: float) -> CalculationResult:
        """Calculate resistance using R = V / I."""

        if current == 0:
            raise InputValidationError("Current cannot be zero.")

        resistance = voltage / current
        if resistance < 0:
            raise InputValidationError("Calculated resistance cannot be negative.")

        return CalculationResult(
            title="Calculate Resistance",
            inputs=(
                DisplayValue("Voltage (V)", f"{format_number(voltage)} V"),
                DisplayValue("Current (I)", f"{format_number(current)} A"),
            ),
            steps=(
                "R = V / I",
                f"R = {format_number(voltage)} / {format_number(current)}",
                f"R = {format_number(resistance)} {OHM_SYMBOL}",
            ),
            result_label="Resistance",
            result_value=f"{format_number(resistance)} {OHM_SYMBOL}",
        )

    @staticmethod
    def power(
        *,
        voltage: float | None = None,
        current: float | None = None,
        resistance: float | None = None,
    ) -> CalculationResult:
        """Calculate power using the best formula for the available values."""

        if resistance is not None and resistance < 0:
            raise InputValidationError("Resistance cannot be negative.")

        inputs: list[DisplayValue] = []
        if voltage is not None:
            inputs.append(
                DisplayValue("Voltage (V)", f"{format_number(voltage)} V")
            )
        if current is not None:
            inputs.append(
                DisplayValue("Current (I)", f"{format_number(current)} A")
            )
        if resistance is not None:
            inputs.append(
                DisplayValue(
                    "Resistance (R)", f"{format_number(resistance)} {OHM_SYMBOL}"
                )
            )

        if voltage is not None and current is not None:
            power = voltage * current
            formula = "P = V x I"
            substitution = (
                f"P = {format_number(voltage)} x {format_number(current)}"
            )
        elif current is not None and resistance is not None:
            power = current**2 * resistance
            formula = "P = I^2 x R"
            substitution = (
                f"P = {format_number(current)}^2 x "
                f"{format_number(resistance)}"
            )
        elif voltage is not None and resistance is not None:
            if resistance == 0:
                raise InputValidationError(
                    "Resistance cannot be zero when using P = V^2 / R."
                )
            power = voltage**2 / resistance
            formula = "P = V^2 / R"
            substitution = (
                f"P = {format_number(voltage)}^2 / "
                f"{format_number(resistance)}"
            )
        else:
            raise InputValidationError(
                "Enter at least one valid pair: V and I, I and R, or V and R."
            )

        return CalculationResult(
            title="Calculate Power",
            inputs=tuple(inputs),
            steps=(
                formula,
                substitution,
                f"P = {format_number(power)} W",
            ),
            result_label="Power",
            result_value=f"{format_number(power)} Watt",
        )

    @staticmethod
    def _require_resistors(resistors: Sequence[float]) -> None:
        if not resistors:
            raise InputValidationError("Enter at least one resistance value.")

    @staticmethod
    def _require_nonnegative_resistance(resistance: float) -> None:
        if resistance < 0:
            raise InputValidationError("Resistance cannot be negative.")

