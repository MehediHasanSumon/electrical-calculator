"""Validation and formatting helpers."""

import math


class InputValidationError(ValueError):
    """Raised when user-entered data cannot be used safely."""


def parse_number(
    text: str,
    *,
    field_name: str = "Value",
    minimum: float | None = None,
    minimum_inclusive: bool = True,
    nonzero: bool = False,
) -> float:
    """Parse and validate a finite floating-point number.

    Args:
        text: Raw user input.
        field_name: Human-readable field name used in error messages.
        minimum: Optional lower bound.
        minimum_inclusive: Whether the lower bound itself is valid.
        nonzero: Whether zero must be rejected.

    Returns:
        A validated finite float.

    Raises:
        InputValidationError: If the input is blank, nonnumeric, or invalid.
    """

    cleaned = text.strip()
    if not cleaned:
        raise InputValidationError(f"{field_name} cannot be blank.")

    try:
        value = float(cleaned)
    except ValueError as exc:
        raise InputValidationError("Invalid input.") from exc

    if not math.isfinite(value):
        raise InputValidationError(f"{field_name} must be a finite number.")

    if nonzero and value == 0:
        raise InputValidationError(f"{field_name} cannot be zero.")

    if minimum is not None:
        below_minimum = value < minimum
        at_excluded_minimum = value == minimum and not minimum_inclusive
        if below_minimum or at_excluded_minimum:
            comparator = "at least" if minimum_inclusive else "greater than"
            raise InputValidationError(
                f"{field_name} must be {comparator} {format_number(minimum)}."
            )

    return value


def parse_number_list(
    text: str,
    *,
    field_name: str = "Value",
    minimum: float | None = None,
    minimum_inclusive: bool = True,
) -> list[float]:
    """Parse a comma-separated list of validated numbers."""

    cleaned = text.strip()
    if not cleaned:
        raise InputValidationError(f"{field_name} values cannot be blank.")

    parts = cleaned.split(",")
    if any(not part.strip() for part in parts):
        raise InputValidationError(
            f"Enter {field_name.lower()} values separated by commas."
        )

    return [
        parse_number(
            part,
            field_name=field_name,
            minimum=minimum,
            minimum_inclusive=minimum_inclusive,
        )
        for part in parts
    ]


def format_number(value: float, decimals: int = 2) -> str:
    """Format a number with fixed precision while keeping integers clean."""

    rounded = round(float(value), decimals)
    if rounded == 0:
        rounded = 0.0

    if rounded.is_integer():
        return str(int(rounded))

    return f"{rounded:.{decimals}f}".rstrip("0").rstrip(".")


def format_step_number(value: float) -> str:
    """Format intermediate calculation values with useful extra precision."""

    return format_number(value, decimals=6)
