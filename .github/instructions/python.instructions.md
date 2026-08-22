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
- Every python file except __init__.py should have the following docstring at the beginning:

```python
r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$  __$$\ $$  __$$\ $$  _____|$$  __$$\                 |
|              $$ /  $$ |$$ |  $$ |$$ |      $$ /  \__|                |
|              $$$$$$$$ |$$$$$$$  |$$$$$\    \$$$$$$\                  |
|              $$  __$$ |$$  __$$< $$  __|    \____$$\                 |
|              $$ |  $$ |$$ |  $$ |$$ |      $$\   $$ |                |
|              $$ |  $$ |$$ |  $$ |$$$$$$$$\ \$$$$$$  |                |
|              \__|  \__|\__|  \__|\________| \______/                 |
|                                                                      |
|              Automated Rapid Embedded Simulation (c)                 |
|______________________________________________________________________|

Copyright 2025 olympus-tools contributors. Dependencies and licenses
are listed in the NOTICE file:

    https://github.com/olympus-tools/ARES/blob/master/NOTICE

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License:

    https://github.com/olympus-tools/ARES/blob/master/LICENSE
"""
```

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

# dict.get() for default values

When retrieving keys from dictionaries use `dict.get(key, default)` to specify default values when keys don't exist. 
More efficient and readable than `try/except` or `if key in dict`.

## References
- [Python Docs - dict.get()](https://docs.python.org/3/library/stdtypes.html#dict.get)

# List Comprehensions over loops

Instead of building lists with for loops, use list comprehensions for more concise code and better performance.
Comprehensions are optimized at the C level and avoid repeated append method calls.

# Sets for sorting, uniqueness
The `in` operator on lists performs O(n) linear search, while sets use O(1) hash-based lookup. 
For memberships checks or for obtaining unique lists/sets, converting to a set provides significant speedup even accounting for conversion cost.

## References
- [Python Docs - Set Types](https://docs.python.org/3/library/stdtypes.html#set)


## References
- [Python Docs - List Comprehensions](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions)

# Numba for performance optimization

When writing Python code that involves heavy mathematical computation, numerical arrays (NumPy), 
or performance-critical loops, automatically consider using Numba (@jit or @njit decorators) to accelerate execution. 
Ensure that functions targeted for JIT compilation are written in a Numba-compatible subset of Python 
(e.g., avoiding unsupported library calls and relying on primitive types or NumPy arrays).

```python
import numpy as np
from numba import njit

# Automatically apply @njit for heavy numerical loops
@njit(cache=True)
def calculate_euclidean_distance_matrix(coords):
    """Compute pairwise Euclidean distance matrix for a set of coordinates."""
    n = coords.shape[0]
    dist_matrix = np.zeros((n, n), dtype=np.float64)
    
    for i in range(n):
        for j in range(i + 1, n):
            d = 0.0
            for k in range(coords.shape[1]):
                diff = coords[i, k] - coords[j, k]
                d += diff * diff
            val = np.sqrt(d)
            dist_matrix[i, j] = val
            dist_matrix[j, i] = val
            
    return dist_matrix
```

## References
- [Numba 5min guide](https://numba.pydata.org/numba-doc/dev/user/5minguide.html)
- [Numba tips](https://numba.pydata.org/numba-doc/dev/user/performance-tips.html)
