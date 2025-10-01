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

# Copyright (c) 2025 Andrä Carotta
#
# Licensed under the MIT License. See the LICENSE file for details.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# You may obtain a copy of the License at
# https://github.com/AndraeCarotta/ares/blob/master/LICENSE

"""

import numpy as np
import pytest

from ares.utils.signal import signal


def test_ares_signal_types():
    """
    Test if ares signal can be initialized without data. And if label and timestamps have the correct datatype.
    """
    test_signal = signal(label="test_signal")

    assert test_signal.label == "test_signal", "label of signal is false."
    assert isinstance(test_signal.timestamps, np.ndarray), (
        "timestamps element of signal is no numpy array."
    )
    assert np.issubdtype(test_signal.timestamps.dtype, np.floating), (
        "timetamps array of signal is not of type float."
    )
    assert isinstance(test_signal.data, np.ndarray), (
        "data element of signal no numpy array."
    )
    assert np.issubdtype(test_signal.data.dtype, np.object_)


def test_ares_signal_init():
    """
    Test if ares signal can be initialized with data.
    """
    test_signal = signal(
        label="test_signal",
        timestamps=np.array([1, 2, 3, 4], dtype=float),
        data=np.array([1, 2, 3, 4], dtype=np.int64),
    )

    assert test_signal.label == "test_signal"
    assert isinstance(test_signal.timestamps, np.ndarray), (
        "timestamps element of signal is no numpy array."
    )
    assert np.issubdtype(test_signal.timestamps.dtype, np.floating), (
        "timetamps array of signal is not of type float."
    )
    assert len(test_signal.timestamps) == 4, "Ops, timstamps length is false."
    assert isinstance(test_signal.data, np.ndarray), (
        "data element of signal no numpy array."
    )
    assert np.issubdtype(test_signal.data.dtype, np.int64)
    assert len(test_signal.data) == 4, "Ops, data length is false."


@pytest.mark.parametrize(
    "label, timestamps, data",
    [
        ("test_signal1", np.zeros((4), dtype=float), np.ones((4), dtype=float)),
        (
            "test_signal2",
            np.array([10, 12, 13, 14, 15], dtype=float),
            np.array([1, 2, 3, 4, 5], dtype=np.int32),
        ),
    ],
)
def test_ares_signal(label, timestamps, data):
    """
    Tests different signal types and lengths.
    """
    test_signal = signal(label=label, timestamps=timestamps, data=data)
    data_length = len(timestamps)

    assert test_signal.label == label
    assert isinstance(test_signal.timestamps, np.ndarray), (
        "timestamps element of signal is no numpy array."
    )
    assert np.issubdtype(test_signal.timestamps.dtype, np.floating), (
        "timetamps array of signal is not of type float."
    )
    assert len(test_signal.timestamps) == data_length, "Ops, timstamps length is false."
    assert isinstance(test_signal.data, np.ndarray), (
        "data element of signal no numpy array."
    )
    assert len(test_signal.data) == data_length, "Ops, data length is false."


if __name__ == "__main__":
    test_ares_signal_types()
