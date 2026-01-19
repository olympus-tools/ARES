---
description: 'Python coding conventions and guidelines'
applyTo: '**/*.py'
---

# Python Coding Conventions

## Python Instructions

- Write clear and concise comments for each function in English.
- Ensure functions have descriptive names and include type hints.
- **Prefer built-in Python types** for type annotations (e.g., `int | float`, `list[str]`, `dict[str, int]`, `tuple[int, ...]`).
- **Use the `typing` module when no suitable built-in type exists** for the required type annotation (e.g., `Callable`, `TypeVar`, `Protocol`, `Any`, `ClassVar`).
- Break down complex functions into smaller, more manageable functions.
- Use @typechecked decorator for methods and functions.
- Use **Pydantic models** for input validation when working with structured data.
- Always handle **edge cases** and raise meaningful exceptions (e.g., `ValueError`).
- Write **pytests** for critical functions and cover positive, negative, and edge cases.

## General Instructions

- Always prioritize readability and clarity. All code, comments, and docstrings must be written in English.
- For algorithm-related code, include explanations of the approach used.
- Write code with good maintainability practices, including comments on why certain design decisions were made.
- Handle edge cases and write clear exception handling.
- For libraries or external dependencies, mention their usage and purpose in comments.
- Use consistent naming conventions and follow language-specific best practices.
- Write concise, efficient, and idiomatic code that is also easily understandable.
- Doc-strings and comments should always be written in clear english.
- Use the `@safely_run` and `@error_msg` decorators from `ares.utils.decorators` for robust error handling and logging in your classes and functions. Pass relevant attributes to `safely_run` (e.g., `include_args`, `instance_el`) to improve context in logs.

## Code Style and Formatting

- Use ruff formatting instructions from pyproject.toml file.

## Edge Cases and Testing

- Always include test cases for critical paths of the application.
- Account for common edge cases like empty inputs, invalid data types, and large datasets.
- Include comments for edge cases and the expected behavior in those cases.
- Write unit tests for functions and document them with docstrings explaining the test cases.

## Example of Proper Documentation

- Always use **Google style** for documentation.
- Include `Args`, `Returns` and when relevant => other sections (e.g. Examples,...) should not be included.
- Use **built-in types** for all arguments and return values where possible.
- Decorate with `@typechecked` and use **Pydantic models** if applicable.
- Imports should always be listed together at the beginning of the Python file.

```python
import math

from pydantic import BaseModel, Field
from typeguard import typechecked
from ares.utils.decorators import safely_run, error_msg


class Circle(BaseModel):
    """Pydantic model for circle input validation."""

    radius: int | float = Field(
        ..., gt=0, description="Radius of the circle, must be > 0"
    )

class CircleCalculator:
    """Example class using @safely_run and @error_msg decorators for robust error handling."""

    def __init__(self, circle: Circle):
        self.circle = circle

    @typechecked
    @safely_run(
        default_return=float('nan'),
        exception_msg="Error in calculate_area: returning NaN.",
        include_args=["self"],
        instance_el=["circle"],
        log=None  # Pass a custom logger instance if desired
    )
    def calculate_area(self) -> float:
        """Calculate the area of the circle.

        Args:
            self (CircleCalculator): Instance containing the circle.

        Returns:
            float: The area of the circle, calculated as π * radius^2.
        """
        if self.circle.radius <= 0:
            raise ValueError("Radius must be greater than zero.")
        return math.pi * self.circle.radius**2

    @typechecked
    @error_msg(
        "Failed to calculate diameter.",
        exception_map={ValueError: "Radius must be positive (ValueError)."},
        include_args=["self"],
        instance_el=["circle"],
        log=None  # Pass a custom logger instance if desired
    )
    def calculate_diameter(self) -> float:
        """Calculate the diameter of the circle.

        Args:
            self (CircleCalculator): Instance containing the circle.

        Returns:
            float: The diameter of the circle, calculated as 2 * radius.
        """
        if self.circle.radius <= 0:
            raise ValueError("Radius must be greater than zero.")
        return 2 * self.circle.radius

def test_circle_calculator():
    """Unit tests for CircleCalculator methods."""
    c1 = Circle(radius=1)
    c2 = Circle(radius=2.5)
    calc1 = CircleCalculator(c1)
    calc2 = CircleCalculator(c2)
    assert abs(calc1.calculate_area() - math.pi) < 1e-9
    assert abs(calc2.calculate_area() - (math.pi * 2.5**2)) < 1e-9
    assert abs(calc1.calculate_diameter() - 2) < 1e-9
    assert abs(calc2.calculate_diameter() - 5) < 1e-9

    CircleCalculator(Circle(radius=0)).calculate_area()
    CircleCalculator(Circle(radius=0)).calculate_diameter()

```
