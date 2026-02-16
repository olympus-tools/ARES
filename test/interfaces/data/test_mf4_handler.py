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

Copyright 2025 olympus-tools contributors. Contributors to this project
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

import os
from pathlib import Path

import numpy as np
import pytest
from asammdf.blocks.utils import MdfException

from ares.interface.data.ares_signal import AresSignal
from ares.interface.data.mf4_handler import MF4Handler


def test_ares_mf4handler_file_init_read():
    """
    Test if mf4handler can be initialized with mf4-file mode "read".
    """
    mf4_filepath = Path(
        os.path.join(
            os.path.dirname(__file__),
            "../../../examples/data/data_example_1.mf4",
        )
    )

    if mf4_filepath.is_file():
        test_data = MF4Handler(
            file_path=mf4_filepath,
        )


def test_ares_mf4handler_file_init_write():
    """
    Test if mf4handler can be initialized with mf4-file mode "write".
    """
    mf4_filepath = Path(os.path.join(os.path.dirname(__file__), "test_file.mf4"))
    test_data_write01 = MF4Handler(file_path=None, signals=[])
    test_data_write01._save(mf4_filepath)

    if not mf4_filepath.is_file():
        assert "Argh. No mf-4-file was created. Check mf4_handler implementation."
    else:
        mf4_filepath.unlink()

    test_data_write02 = MF4Handler(file_path=None, signals=[])
    test_data_write02._save(mf4_filepath)

    if not mf4_filepath.is_file():
        assert "Argh. No mf-4-file was created. Check mf4_handler implementation."
    else:
        mf4_filepath.unlink()

    # WARN: The following part in the test leads to an recursion in asammdf. This is on purpose!
    with pytest.raises(MdfException):
        test_data_read = MF4Handler(file_path=mf4_filepath)


def test_ares_mf4handler_file_read_get():
    """
    Test if mf4handler can read signals from mf4-files.
    """
    mf4_filepath = Path(
        os.path.join(
            os.path.dirname(__file__),
            "../../../examples/data/data_example_1.mf4",
        )
    )

    if mf4_filepath.is_file():
        test_data = MF4Handler(
            file_path=mf4_filepath,
        )

    test_signal = test_data.get(["input_value"])
    test_signals = test_data.get([".*_"])

    assert len(test_signal) == 1, "Wrong number of signals were extracted."
    assert test_signal[0].label == "input_value", "The wrong signal was extracted."
    assert len(test_signals) != 1, (
        "Too few singals were extracted. Regex pattern should extract all available signals."
    )


def test_ares_mf4handler_file_write_get():
    """
    Test if mf4handler can read signals from created mf4-file.
    """
    mf4_filepath = Path(os.path.join(os.path.dirname(__file__), "test_file.mf4"))

    test_signal = AresSignal(
        label="test_signal",
        timestamps=np.array([1, 2, 3, 4], dtype=np.float32),
        value=np.array([1, 2, 3, 4], dtype=np.int64),
    )

    test_data_write = MF4Handler(file_path=None, data=[test_signal])
    test_signal_read = test_data_write.get()

    assert len(test_signal_read) == 1, (
        "Wrong number of signals were extracted after write."
    )
    assert test_signal_read[0].label == "test_signal", (
        "The wrong signal label was written."
    )

    test_data_write._save(mf4_filepath)
    if not mf4_filepath.is_file():
        assert "Argh. No mf-4-file was created. Check mf4_handler implementation."
    else:
        mf4_filepath.unlink()
