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

import datetime
from pathlib import Path


def eval_output_path(
    output_hash: str,
    output_dir: Path,
    output_format: str,
    wf_element_name: str,
) -> Path:
    """Generate output file path with timestamp to prevent overwriting.

    Creates a timestamped filename in the format: {wf_element_name}_{hash}_{YYYYMMDDHHMMSS}.{format}
    and ensures the output directory exists.

    Args:
        output_hash (str): Content hash to include in filename
        output_dir (Path): Output directory path (will be created if not exists)
        output_format (str): File format/extension (without dot, e.g., 'dcm', 'json')
        wf_element_name (str): Element name to include in filename

    Returns:
        Path: Complete absolute file path
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    new_file_name = f"{wf_element_name}_{output_hash[:8]}_{timestamp}.{output_format}"
    output_path = output_dir / new_file_name

    return output_path
