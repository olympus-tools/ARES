
# mat_interface

This package provides a standalone interface for reading and writing MATLAB MAT-files. It supports reading version v7.3 (HDF5) via `h5py` and older versions (v7.0 and lower) via `scipy.io.loadmat`. The `get` method intelligently determines the MAT-file version and uses the appropriate backend for reading.
The default `write` function specifically targets v7.3 files. 
It is designed for easy usage with minimal dependencies.

## Usage

To use this interface, you can import the `MatInterface` class and call its static methods.

```python
from pathlib import Path
from mat_interface.mat_interface import MatInterface
import numpy as np

# Example: Writing a MAT file
signals_to_write = [
    {
        'label': 'signal1',
        'timestamps': np.array([0.0, 1.0, 2.0]),
        'value': np.array([10, 20, 30])
    },
    {
        'label': 'signal2',
        'timestamps': np.array([0.0, 1.0, 2.0]),
        'value': np.array([[1, 2], [3, 4], [5, 6]])
    }
]
output_file = Path('output.mat')
MatInterface.write(output_path=output_file, signals=signals_to_write)

# Example: Reading a MAT file
signals_read = MatInterface.get(file_path=output_file)
print(signals_read)

# Example: Reading specific signals from a struct
signals_from_struct = MatInterface.get(file_path=output_file, struct_name=['my_struct'])

# Example: Reading signals with a label filter
signal_1_data = MatInterface.get(file_path=output_file, label_filter=['signal1'])
```

## Supported Data Layouts

The `MatInterface` supports two primary layouts when reading MAT files.

### 1. Timeseries Struct Layout (Default for `write`)
Each signal is encapsulated in its own group containing its specific time vector and data.

```text
/ (root or struct_group)
├── signal_1/
│   ├── Time  (dataset: 1-D timestamps)
│   ├── Data  (dataset: N-D values)
│   └── Events (group: empty, necessary metadata for MATLAB)
└── signal_2/
    ├── Time  (dataset: 1-D timestamps)
    ├── Data  (dataset: N-D values)
    └── Events (group: empty, necessary metadata for MATLAB)
```

### 2. Flat Signal Arrays
Signals are stored as datasets at the same level, sharing a common timestamp vector.

```text
/ (root or struct_group)
├── signal_1    (dataset: N-D values)
├── signal_2    (dataset: N-D values)
└── timestamps  (dataset: 1-D shared timestamps, can also be named 'time')
```

### 3. Nested Struct Layout (via `struct_name`)
The interface can target signals nested within MATLAB structs (HDF5 groups). Within a single targeted struct, all signals must follow the **same** layout; combining layouts within one struct is not supported.

#### Layout: Struct with Flat Signals
All datasets within the struct share a common timestamp vector.

```text
/ (root)
└── my_struct_A/   <-- Targeted via struct_name=['my_struct_A']
    ├── signal_1   (dataset: N-D values)
    ├── signal_2   (dataset: N-D values)
    └── timestamps (dataset: 1-D shared timestamps)
```

#### Layout: Struct with Timeseries Groups
Each signal within the struct is its own group containing its specific time vector.

```text
/ (root)
└── my_struct_B/   <-- Targeted via struct_name=['my_struct_B']
    ├── signal_1/
    │   ├── Time
    │   └── Data
    └── signal_2/
        ├── Time
        └── Data
```

## API Documentation

### `MatInterface.write(output_path: Path, signals: list[dict[str, str | np.typing.NDArray[np.generic]]]) -> None`

*   **Description:** Writes a list of signals to a MAT 7.3 file (HDF5). Each signal is stored as a top-level HDF5 group containing 'Time', 'Data', and 'Events' members ('Events' can be ignored, just for MATLAB compatibility). 
Additional the group carries `MATLAB_class = "timeseries"` and `MATLAB_fields` attributes for MATLAB compatibility.
*   **Parameters:**
    *   `output_path` (Path): The path to the output MAT file.
    *   `signals` (list[dict]): A list of dictionaries, where each dictionary represents a signal and must contain:
        *   `'label'` (str): The name of the signal.
        *   `'timestamps'` (np.ndarray): A 1-D NumPy array of timestamps (float).
        *   `'value'` (np.ndarray): A 1-D, 2-D, or 3-D NumPy array representing the signal's values. The dtype will be mapped to a corresponding MATLAB numerical type.
*   **Note:** This method adds MATLAB-specific headers and attributes for compatibility. MATLAB's `load()` will recognize the structure, but true MATLAB `timeseries` objects require MATLAB's MCOS serialization, which cannot be produced from Python.

### `MatInterface.get(file_path: Path, label_filter: list[str] | None = None, struct_name: list[str] | None = None) -> list[dict[str, str | np.typing.NDArray[np.generic]]]`

*   **Description:** Reads signals from a MAT 7.3 or lower file. It intelligently determines the MAT-file version and uses either `h5py` for v7.3 (HDF5) files or `scipy.io.loadmat` for older versions. It supports 2 different data layouts:
    *   **Timeseries struct layout:** Each signal is a group containing 'Time' and 'Data' sub-datasets.
    *   **Flat signal arrays:** Signals are top-level datasets, with timestamps assumed to be in a separate dataset named 'timestamps' or 'time'.
    It can optionally filter signals by `label_filter` or by reading from specific `struct_name` groups within the MAT file.
*   **Parameters:**
    *   `file_path` (Path): The path to the MAT file to read.
    *   `label_filter` (list[str] | None, optional): A list of signal names (labels) to filter and read. If `None`, all readable signals are returned.
    *   `struct_name` (list[str] | None, optional): A list of struct group names within the MAT file from which to extract signals. If `None`, signals are read from the root level of the MAT file.
*   **Returns:** A list of dictionaries, where each dictionary represents a signal and contains:
    *   `'label'` (str): The name of the signal.
    *   `'timestamps'` (np.ndarray | None): A 1-D NumPy array of timestamps, or `None` if not found.
    *   `'value'` (np.ndarray): A NumPy array containing the signal's values.
*   **Note:** This method does not support MATLAB MCOS `timeseries` objects due to their opaque serialization. It also skips internal HDF5 groups like `#refs#` and `#subsystem#`.
