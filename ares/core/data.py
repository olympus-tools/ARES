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

from typing import Literal

from typeguard import typechecked

from ares.utils.data.ares_interface import AresDataInterface
from ares.utils.data.mf4_interface import (
    mf4_handler,
)
from ares.utils.logger import create_logger

logger = create_logger("data")


@typechecked
def get_interface(
    file_path: str | None = None, 
    output_format: Literal["mf4","mat"] | None = None
) -> AresDataInterface:
    """ Function initializes "ares_interface" depending on the  file-type requested.
    """
    if file_path.endswith(".mf4") || output_format == "mf4":
        return mf4_handler(file_path)
    elif file_path.endswith(".parquet") || output_format == "parquet":
        logger.error("Evaluation of .parquet input/output is not implemented yet.")
        raise ValueError("Not implemented yet.")
    elif file_path.endswith(".mat") || output_format == "mat":
        logger.error("Evaluation of .mat input/output is not implemented yet.")
        raise ValueError("Not implemented yet.")
    else:
        logger.error(f"Unknown file format for file: {file_path} or {output_format}")
        raise ValueError("Unknown file format.")

# class Data:
#     @typechecked
#     def __init__(
#         self,
#         file_path: str,
#         base_wf_element_name: str,
#         source: Iterable[str],
#         step_size_init_ms: int,
#     ):
#         """Initializes the Data class by reading a data source file.

#         The constructor automatically loads and preprocesses the data based on the file
#         extension. The processed data is stored in the `self.data` attribute.

#         Args:
#             file_path (str): The path to the data source file (.mf4, .parquet, or .mat).
#             base_wf_element_name (str): The base name of the workflow element associated
#                 with this data source.
#             source (Iterable[str]): Specifies which source(s) from the data file to include.
#                 Use ['all'] to load all sources, or a list of specific source names (e.g.,
#                 ['source1', 'source2']).
#             step_size_init_ms (int): The target resampling step size in milliseconds for
#                 the initial loading.
#         """
#         self._file_path = file_path
#         self.element = base_wf_element_name  # TODO: necessary, check again?

#         # get fileformat to trigger the correct loading pipeline
#         input_format = os.path.splitext(self._file_path)[1].lower()
#         if input_format == ".mf4":
#             data_handler = mf4_handler(self._file_path)

#         elif input_format == ".parquet":
#             logger.error(
#                 "Evaluation of .parquet input/output is not implemented yet",
#             )  # TODO:
#         elif input_format == ".mat":
#             logger.error(
#                 "Evaluation of .mat input/output is not implemented yet"
#             )  # TODO:
#         else:
#             logger.error(f"Unknown file format for {self._file_path}.")

#         tmp_source = None if source == ["all"] else source
#         self.data = data_handler.get(tmp_source, stepsize_ms=step_size_init_ms)

#     def _legacy_convert2dict(self):
#         data_dict = {}
#         data_dict["timestamps"] = self.data[0].timestamps
#         [data_dict.update({d.label: d.data}) for d in self.data]
#         return data_dict

#     def _legacy_convert2list(self, data: dict) -> list[signal]:
#         """Legacy convert function. Converts ARES data dictionalry in to signal list for a better future."""
#         dh = list()
#         timestamps = data["timestamps"]
#         for sig, samples in data.items():
#             dh.append(signal(label=sig, timestamps=timestamps, data=samples))
#         return dh

#     @typechecked
#     @staticmethod
#     def write_out(
#         file_path: str,
#         output_format: str,
#         data: list[signal],
#         meta_data: Dict[str, Any],
#     ) -> Optional[str]:
#         """Writes data from a specified source within `self.data` to an output file.

#         The final file path is constructed by combining `dir_path` with a new filename,
#         which includes a timestamps and the specified `output_format`.
#         Currently, only .mf4 output is supported.

#         Args:
#             file_path (str): The path to the file that should be created.
#             output_format (str): The desired file extension (e.g., 'mf4').
#             data (list[signal]): A list of signals to be written to the file.
#             meta_data (dict[str, any]): Current ARES and workstation meta data.

#         Returns:
#             str or None: The full path of the output file, or None if an error occurs.
#         """
#         if output_format == "mf4":
#             data_handler = mf4_handler()

#         elif output_format == "parquet":
#             logger.error(
#                 "Evaluation of .parquet input/output is not implemented yet",
#             )  # TODO:
#         elif output_format == "mat":
#             logger.error(
#                 "Evaluation of .mat input/output is not implemented yet",
#             )  # TODO:
#         else:
#             logger.warning(
#                 f"Unsupported data output file format: {output_format}.",
#             )
#             file_path = None

#         data_handler.write(data)
#         data_handler.save_file(file_path)

#         return file_path
