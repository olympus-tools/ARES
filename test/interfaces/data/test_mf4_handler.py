r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$  __$$\ $$  __$$\ $$  _____|$$  __$$\                 |
|              $$ /  $$ |$$ |  $$ |$$ |      $$ /  \__|                |
|              $$$$$$$$ |$$$$$$$  |$$$$$\    \$$$$$$\                  |
|              $$ |  $$ |$$ |  $$ |$$ |      $$\   $$ |                |
|              $$ |  $$ |$$ |  $$ |$$$$$$$$\ \$$$$$$  |                |
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

import os
from pathlib import Path

import numpy as np

from ares.interface.data.ares_signal import AresSignal
from ares.interface.data.mf4_handler import MF4Handler


# TEST: MF4Handler read mode
def test_ares_mf4handler_file_init_read():
    """
    Tests if mf4handler can be initialized with mf4-file mode "read".
    """
    mf4_filepath = Path(
        os.path.join(
            os.path.dirname(__file__),
            "../../../examples/data/data_example_1.mf4",
        )
    )

    test_data = MF4Handler(file_path=mf4_filepath)

    assert "input_value" in test_data._available_signals


def test_ares_mf4handler_file_read_get():
    """
    Tests if mf4handler can read signals from mf4-files.
    """
    mf4_filepath = Path(
        os.path.join(
            os.path.dirname(__file__),
            "../../../examples/data/data_example_1.mf4",
        )
    )

    test_data = MF4Handler(file_path=mf4_filepath)

    test_signal = test_data.get(["input_value"])
    test_signals = test_data.get([".*_"])

    assert len(test_signal) == 1, "Wrong number of signals were extracted."
    assert test_signal[0].label == "input_value", "The wrong signal was extracted."
    assert len(test_signals) != 1, (
        "Too few signals were extracted. Regex pattern should extract all available signals."
    )


# TEST: MF4Handler write mode
def test_ares_mf4handler_file_init_write(tmp_path):
    """
    Tests if mf4handler can be initialized with mf4-file mode "write".

    Args:
        tmp_path (Path): pytest fixture providing a temporary directory.
    """
    mf4_filepath = tmp_path / "test_file.mf4"

    test_data_write01 = MF4Handler(file_path=None)
    test_data_write01._save(mf4_filepath)

    assert mf4_filepath.is_file(), (
        "Argh. No mf-4-file was created. Check mf4_handler implementation."
    )

    # NOTE: Since asammdf 8.7.x, saving an empty MDF produces a valid mf4-file
    # that loads cleanly without any signals.
    test_data_read = MF4Handler(file_path=mf4_filepath)

    assert not test_data_read._available_signals, (
        "Saved empty mf4-file should not contain any signals."
    )


def test_ares_mf4handler_file_write_get(tmp_path):
    """
    Tests if mf4handler can read signals from created mf4-file.

    Args:
        tmp_path (Path): pytest fixture providing a temporary directory.
    """
    mf4_filepath = tmp_path / "test_file.mf4"

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
    assert mf4_filepath.is_file(), (
        "Argh. No mf-4-file was created. Check mf4_handler implementation."
    )
