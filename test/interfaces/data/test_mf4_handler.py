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

import os

import pytest

from ares.interface.data.mf4_handler import MF4Handler


def test_ares_mf4handler_file_init_read():
    """
    Test if mf4handler can be initialized with mf4-file mode "read".
    """
    mf4_filepath = os.path.join(
        os.path.dirname(__file__),
        "../../../examples/data/data_example_1.mf4",
    )

    if os.path.isfile(mf4_filepath):
        test_data = MF4Handler(
            file_path=mf4_filepath,
        )


def test_ares_mf4handler_file_init_write():
    """
    Test if mf4handler can be initialized with mf4-file mode "write".
    """
    mf4_filepath = os.path.join(os.path.dirname(__file__), "test_file.mf4")
    test_data_write = MF4Handler(file_path=mf4_filepath, mode="write")
    test_data_write.write(mf4_filepath)

    if not os.path.isfile(mf4_filepath):
        assert "Argh. No mf4-file was created. Check mf4_handler implementation."
    else:
        os.remove(mf4_filepath)

    # WARN: The following part in the test leads to an recursion in asammdf. This is on purpose!
    with pytest.raises(FileNotFoundError):
        test_data_read = MF4Handler(file_path=mf4_filepath, mode="read")


if __name__ == "__main__":
    test_ares_mf4handler_file_init_read()
