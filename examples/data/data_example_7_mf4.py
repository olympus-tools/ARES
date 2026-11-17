r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$  __$$\ $$ |  $$ |$$  _____|$$ /  \__|                |
|              $$ /  $$ |$$ |  $$ |$$ |      $$\   $$ |                |
|              $$$$$$$$ |$$$$$$$  |$$$$$\    \$$$$$$\                  |
|              $$  __$$ |$$  __$$< $$  __|    \____$$\                 |
|              $$ |  $$ |$$ |  $$ |$$ |      $$\   $$ |                |
|              $$$$$$$$ |$$ |  $$ |$$$$$$$$\ \$$$$$$  |                |
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

    https://www.apache.org/licenses/LICENSE-2.0
"""

from pathlib import Path

import numpy as np
from asammdf import MDF, Signal, Source

source_1 = Source(
    name="source_1",
    path="source_1",
    comment="Data source 1 for ares example",
    source_type=1,
    bus_type=1,
)

# Use the same time base and input values as data_example_1_2_mf4.py.
step_size = 1.0
timestamps = np.arange(0.0, 20.0, step_size)
input_samples = np.where(timestamps >= 10, 1, 0).astype(np.float32)

input_value = Signal(
    samples=input_samples,
    timestamps=timestamps,
    name="input_value",
    source=source_1,
    comment=f"Input signal with step at 10s and step size {step_size}s",
)

filter_output = Signal(
    samples=np.full_like(input_samples, -1.0),
    timestamps=timestamps,
    name="filter_output",
    source=source_1,
    comment=f"Constant filter output with step size {step_size}s",
)

mdf = MDF()
mdf.append(input_value)
mdf.append(filter_output)

output_dir = Path("examples/data")
file_path = output_dir / "data_example_7.mf4"
output_dir.mkdir(parents=True, exist_ok=True)
mdf.save(file_path, overwrite=True)

print(f"MF4 data source created and saved at: {file_path}")
