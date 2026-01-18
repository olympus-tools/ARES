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

from pathlib import Path

import numpy as np
from asammdf import MDF, Signal, Source

# 1. Create a Source object with a name and a path for traceability
source_1 = Source(
    name="source_1",
    path="source_1",
    comment="Data source 1 for ares example",
    source_type=1,
    bus_type=1,
)

# 2. Create the Signal objects with individual timestamp arrays

# 2.1 input_value signal
# Timestamps: 0.0s to 19.0s, step 1.0s (20 samples)
timestamps_input = np.arange(0.0, 20.0, 1.0)
samples_input = np.where(timestamps_input >= 10, 1, 0)
input_value = Signal(
    samples=samples_input,
    timestamps=timestamps_input,
    name="input_value",
    source=source_1,
    comment="",
)

# 2.2 signal_scalar - scalar int32 signal
# Timestamps: 0.0s to 19.5s, step 0.5s (40 samples)
timestamps_scalar = np.arange(0.0, 20.0, 0.5)
signal_scalar_samples = np.arange(len(timestamps_scalar), dtype=np.int32)
signal_scalar = Signal(
    samples=signal_scalar_samples,
    timestamps=timestamps_scalar,
    name="signal_scalar",
    source=source_1,
    comment="Scalar int32 signal for inout_handling example",
)

# 2.3 signal_array1d - 1D array with 4 elements (float64)
# Timestamps: 0.0s to 19.5s, step 0.5s (40 samples)
timestamps_array1d = np.arange(0.0, 20.0, 0.5)
signal_array1d_samples = np.zeros((len(timestamps_array1d), 4), dtype=np.float64)
for i in range(len(timestamps_array1d)):
    signal_array1d_samples[i] = [i * 1.0, i * 2.0, i * 3.0, i * 4.0]

types_1d = [("signal_array1d_xyz", "(4,)<f8")]
signal_array1d = Signal(
    samples=np.rec.fromarrays([signal_array1d_samples], dtype=np.dtype(types_1d)),
    timestamps=timestamps_array1d,
    name="signal_array1d_xyz",
    unit="A",
    source=source_1,
    comment="1D array signal (4 elements) per time step",
)

# 2.4 signal_array2d - 2D array with 2x3 elements (float64)
# Timestamps: 0.0s to 19.5s, step 0.5s (40 samples)
timestamps_array2d = np.arange(0.0, 20.0, 0.5)
signal_array2d_samples = np.zeros((len(timestamps_array2d), 2, 3), dtype=np.float64)
for i in range(len(timestamps_array2d)):
    signal_array2d_samples[i] = [
        [i * 1.0, i * 2.0, i * 3.0],
        [i * 4.0, i * 5.0, i * 6.0],
    ]

types_2d = [("signal_array2d", "(2, 3)<f8")]
signal_array2d = Signal(
    samples=np.rec.fromarrays([signal_array2d_samples], dtype=np.dtype(types_2d)),
    timestamps=timestamps_array2d,
    name="signal_array2d",
    unit="N",
    source=source_1,
    comment="2D array signal (2x3 elements) per time step",
)

# 3. Create a new MDF file and append all signals
mdf = MDF()
mdf.append(input_value)
mdf.append(signal_scalar)
mdf.append(signal_array1d)
mdf.append(signal_array2d)

# 4. Define the output path and save the file
output_dir = Path("examples/data")
file_name = "data_example_3.mf4"
file_path = output_dir / file_name

# Create the examples directory if it doesn't exist
output_dir.mkdir(parents=True, exist_ok=True)

# Save the MDF object to the specified file path
mdf.save(file_path, overwrite=True)

print(
    f"Signals 'input_value', 'signal_scalar', 'signal_array1d', 'signal_array2d' successfully created and saved to '{file_path}'."
)
