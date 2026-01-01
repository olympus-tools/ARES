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

Copyright 2025 Andrä Carotta

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

For details, see: https://github.com/AndraeCarotta/ares#7-license
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import numpy.typing as npt


@dataclass
class AresParameter:
    """A class to handle simulation parameters with numpy arrays of different dimensions.

    This class provides a unified interface for handling simulation parameters
    that can be scalar values, 1D arrays, or 2D arrays. It automatically
    converts input values to numpy arrays.

    Attributes:
        label: Name or identifier of the parameter (required).
        value: The parameter value as numpy array - can be scalar (0D), 1D, or 2D (required).
        description: Optional textual description of the parameter.
        unit: Optional physical unit of the parameter (e.g., 'km/h', '°C', 'm/s').
    """

    label: str
    value: npt.NDArray
    description: Optional[str] = None
    unit: Optional[str] = None

    def __post_init__(self) -> None:
        """Post-initialization processing.

        Converts the value to a numpy array if it isn't one already.
        Accepts scalars, lists, tuples, and existing numpy arrays.
        """
        if not isinstance(self.value, np.ndarray):
            self.value = np.array(self.value)

    @property
    def dtype(self) -> np.dtype:
        """Returns the numpy dtype of the parameter value.

        Returns:
            np.dtype: The data type of the underlying numpy array (e.g., float64, int32).
        """
        return self.value.dtype

    @property
    def shape(self) -> tuple:
        """Returns the shape of the parameter value.

        Returns:
            tuple: The shape of the underlying numpy array.
                   () for scalar, (n,) for 1D array, (m, n) for 2D array.
        """
        return self.value.shape

    @property
    def ndim(self) -> int:
        """Returns the number of dimensions of the parameter value.

        Returns:
            int: The number of dimensions of the underlying numpy array.
                 0 for scalar, 1 for 1D array, 2 for 2D array.
        """
        return self.value.ndim
