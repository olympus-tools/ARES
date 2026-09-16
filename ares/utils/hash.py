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

import hashlib
from dataclasses import fields
from pathlib import Path
from typing import Any

import numpy as np

from ares.utils.decorators import error_msg
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

ENDIAN_TYPE = "big"
CHUNK_SIZE = 4096
BYTE_SIZE = 8

logger = create_logger(name=__name__)


def bin_based_hash(file_path: Path) -> str:
    """Calculate a SHA-256 hash from a binary file's contents.

    Reads the file in chunks to efficiently handle large files without
    loading the entire content into memory.

    Args:
        file_path (Path): Path to the file to hash.

    Returns:
        str: Hexadecimal SHA-256 digest of the file contents.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()


def str_based_hash(input_string: str) -> str:
    """Calculate a SHA-256 hash from a UTF-8 encoded string.

    Args:
        input_string (str): The string to hash.

    Returns:
        str: Hexadecimal SHA-256 digest of the encoded string.
    """
    sha256 = hashlib.sha256(input_string.encode("utf-8"))
    return sha256.hexdigest()


@error_msg(
    exception_msg="Signals hash could not be calculated.",
    log=logger,
)
@typechecked
def dataobject_based_hash(dataobjects: list[Any]) -> str:
    """Calculate a SHA-256 hash from a list of dataobjects using streaming binary encoding.

    Streaming ensures memory usage stays bounded independent of data size,
    with no unnecessary copies of the data or intermediate buffers created.

    Args:
        dataobjects (list[Any]): List of dataclass instances (e.g. AresSignal or AresParameter) to hash.

    Returns:
        str: Hexadecimal SHA-256 digest of the encoded signal data.
    """

    @typechecked
    def _update_hasher(hasher, data: bytes) -> None:
        """Update hasher based on given binary data considering length.

        Args:
            hasher: Open SHA-256 hasher.
            data (bytes): Raw bytes of the field value.
        """
        hasher.update(len(data).to_bytes(BYTE_SIZE, byteorder=ENDIAN_TYPE))
        hasher.update(data)

    @typechecked
    def _update_hasher_numpy(hasher, array: np.ndarray) -> None:
        """Stream a numpy array into the hasher as raw binary data.

        The array is normalized to be C-contiguous using numpy functionality
        (e.g. ensure row-major for transposed arrays or avoid gaps in array slices).
        Additionally the byte order is checked (*.isnative compares data order with system)
        and adapts if necessary.
        This ensures 'minimal' copy since the hasher gets the current values streamed and only byte order updates
        need copy operations.

        The shape and dtype are always hashed before the raw buffer so the encoding
        stays self-delimiting and collision-resistant.

        Args:
            hasher: Open SHA-256 hasher.
            array (np.ndarray): Numpy array to hash.
        """
        array = np.ascontiguousarray(array)
        if not array.dtype.isnative:
            array = array.astype(array.dtype.newbyteorder("="))

        _update_hasher(hasher, str(array.dtype).encode("utf-8"))
        _update_hasher(hasher, repr(array.shape).encode("utf-8"))

        hasher.update(array.nbytes.to_bytes(BYTE_SIZE, byteorder=ENDIAN_TYPE))
        hasher.update(array)

    hasher = hashlib.sha256()
    hasher.update(len(dataobjects).to_bytes(BYTE_SIZE, byteorder=ENDIAN_TYPE))

    for dataobject in dataobjects:
        for field in fields(dataobject):
            value = getattr(dataobject, field.name)
            if value is None:
                _update_hasher(hasher, b"")
            elif isinstance(value, str):
                _update_hasher(hasher, value.encode("utf-8"))
            elif isinstance(value, np.ndarray):
                _update_hasher_numpy(hasher, value)
            else:
                raise TypeError(
                    f"Cannot hash field '{field.name}' of type {type(value)!r}."
                )

    return hasher.hexdigest()
