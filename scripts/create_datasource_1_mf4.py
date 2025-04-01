import numpy as np
from asammdf import MDF, Signal, Source
from pathlib import Path

# 1. Create data and timestamps
# An array for the timestamps with 1s interval (0, 1, 2, ... 19)
timestamps = np.arange(20)

# Create an array for the signal values.
# The value is 0 for all timestamps < 10 and 1 for all timestamps >= 10.
samples = np.where(timestamps >= 10, 1, 0)

# Create a Source object with a name and a path for traceability
source_1 = Source(
    name="source_1",
    path="source_1",
    comment="Data source 1 for ares example",
    source_type=1,
    bus_type=1,
)

# 2. Create the Signal object
signal_input_value = Signal(
    samples=samples,
    timestamps=timestamps,
    name="input_value",
    source=source_1,
    comment="",
)

# 3. Create a new MDF file and define the source
mdf = MDF()
# Append the signal, explicitly linking it to the source
mdf.append(signal_input_value)

# 4. Define the output path and save the file
output_dir = Path("examples")
file_name = "datasource_1.mf4"
file_path = output_dir / file_name

# Create the examples directory if it doesn't exist
output_dir.mkdir(parents=True, exist_ok=True)

# Save the MDF object to the specified file path
mdf.save(file_path, overwrite=True)

print(
    f"Signal 'input_value' successfully created with source 'source_1' and saved to '{file_path}'."
)
