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
step_size_scalar = 1.0
signal_name_scalar = "input_value"

timestamps_input = np.arange(0.0, 20.0, step_size_scalar)
samples_input = np.where(timestamps_input >= 10, 1, 0).astype(np.float32)
signal_scalar = Signal(
    samples=samples_input,
    timestamps=timestamps_input,
    name=signal_name_scalar,
    source=source_1,
    comment=f"Scalar float32 input signal with step at 10s and step size {step_size_scalar}s",
)

# 2.3 signal_array1d - 1D array with 4 elements (float64)
# Timestamps: 0.0s to 19.5s, step 0.5s (40 samples)
step_size_array1d = 0.5
signal_name_array1d = "signal_array1d_xyz"

timestamps_array1d = np.arange(0.0, 30.0, step_size_array1d)
signal_array1d_samples = np.zeros((len(timestamps_array1d), 4), dtype=np.float64)
for i in range(len(timestamps_array1d)):
    signal_array1d_samples[i] = [i * 1.0, i * 2.0, i * 3.0, i * 4.0]

types_1d = [(f"{signal_name_array1d}", "(4,)<f8")]
signal_array1d = Signal(
    samples=np.rec.fromarrays([signal_array1d_samples], dtype=np.dtype(types_1d)),
    timestamps=timestamps_array1d,
    name=signal_name_array1d,
    unit="A",
    source=source_1,
    comment=f"1D array signal (4 elements) per time step with step size {step_size_array1d}s",
)

# 2.4 signal_array2d - 2D array with 2x3 elements (float64)
# Timestamps: 0.0s to 19.5s, step 0.5s (40 samples)
step_size_array2d = 0.7
signal_name_array2d = "signal_array2d"

timestamps_array2d = np.arange(0.0, 20.0, step_size_array2d)
signal_array2d_samples = np.zeros((len(timestamps_array2d), 2, 3), dtype=np.float64)
for i in range(len(timestamps_array2d)):
    signal_array2d_samples[i] = [
        [i * 1.0, i * 2.0, i * 3.0],
        [i * 4.0, i * 5.0, i * 6.0],
    ]

types_2d = [(f"{signal_name_array2d}", "(2, 3)<f8")]
signal_array2d = Signal(
    samples=np.rec.fromarrays([signal_array2d_samples], dtype=np.dtype(types_2d)),
    timestamps=timestamps_array2d,
    name=signal_name_array2d,
    unit="N",
    source=source_1,
    comment=f"2D array signal (2x3 elements) per time step with step size {step_size_array2d}s",
)

# 3. Create a new MDF file and append all signals
mdf = MDF()
mdf.append(signal_scalar)
mdf.append(signal_array1d)
mdf.append(signal_array2d)

output_dir = Path("examples/data")

file_name = "data_example_3.mf4"
file_path = output_dir / file_name
output_dir.mkdir(parents=True, exist_ok=True)
mdf.save(file_path, overwrite=True)

print(f"MF4 data source created and saved at: {file_path}")
