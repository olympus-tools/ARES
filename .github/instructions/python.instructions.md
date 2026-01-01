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


class Circle(BaseModel):
    """Pydantic model for circle input validation."""

    radius: int | float = Field(
        ..., gt=0, description="Radius of the circle, must be > 0"
    )


@typechecked
def calculate_area(radius: int | float) -> float:
    """Calculate the area of a circle given the radius.

    Args:
        radius (int | float): The radius of the circle. Must be positive.

    Returns:
        float: The area of the circle, calculated as π * radius^2.
    """
    if radius <= 0:
        raise ValueError("Radius must be greater than zero.")
    return math.pi * radius**2


def test_calculate_area():
    """Unit tests for calculate_area function."""
    assert abs(calculate_area(1) - math.pi) < 1e-9
    assert abs(calculate_area(2.5) - (math.pi * 2.5**2)) < 1e-9

    try:
        calculate_area(0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for radius = 0")
