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

import ctypes
import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ares.utils.decorators import safely_run
from ares.utils.hash import bin_based_hash
from ares.utils.logger import create_logger

logger = create_logger(name=__name__)

# environment variables to adapt behavior
OVERRIDE_ENV = "ARES_SIM_RUNNER"
CACHE_ENV = "ARES_SIM_RUNNER_CACHE"
COMPILER_ENV = "ARES_CC"
COMPILER_CANDIDATES = ("cc", "gcc", "clang")

# ctypes prototypes mirroring the C types declared in `sim_interface.h`.
GFUNCTYPE = ctypes.CFUNCTYPE(None)  # GlobalSimFunc
PROGRESS_CB = ctypes.CFUNCTYPE(None, ctypes.c_int)  # ProgressCb(int step_idx)


class CSignalMapping(ctypes.Structure):
    """Struct connecting ARES data memory and a simulation unit input global.

    Field names and layout must match `struct SignalMapping` in
    `sim_interface.h`.
    """

    _fields_ = [
        ("data_buffer", ctypes.c_void_p),
        ("target_global", ctypes.c_void_p),
        ("num_bytes", ctypes.c_size_t),
        ("write_once", ctypes.c_bool),
    ]


class CSignalList(ctypes.Structure):
    """Ordered list of signal mappings datatype.

    Field names and layout must match ``struct SignalList`` in
    ``sim_interface.c``.
    """

    _fields_ = [
        ("signals", ctypes.POINTER(CSignalMapping)),
        ("num_signals", ctypes.c_int),
    ]


@dataclass
class PSignalMapping:
    """Python-side description of one signal mapping.

    Args:
        data_buffer: Address (int) of the C-contiguous ARES buffer whose first
            axis is the time dimension. Row source for inputs, row sink for
            outputs.
        target_global: Address (int) of the simulation unit's global variable.
        num_bytes: Bytes transferred per time step (= itemsize * element count).
        write_once: When True the copy happens once before the loop. Only valid
            for inputs; ``data_buffer`` then points at the single value/array.
    """

    data_buffer: int
    target_global: int
    num_bytes: int
    write_once: bool = False


def build_signal_list(entries: list[PSignalMapping]) -> tuple[CSignalList, object]:
    """Pack `PSignalMapping` descriptions into a :class:`CSignalList`.

    Returning the CSignalMapping along the CSignalList avoids the garbage collector
    to clean up the arrays. Pointer stay valid.

    Args:
        entries (list[PSignalMapping]): List of PythonSide AresSignals mapped for the c-call.

    Returns:
        tuple (tuple[CSignalList, object]): Tuple containing CSignalList and CSignalMapping of corresponding size.
                                            'object' is necessary since CSignalMapping size changes.
    """
    array = (CSignalMapping * len(entries))()  # Allocating memory for the signals
    for i, entry in enumerate(entries):
        slot = array[i]
        slot.data_buffer = entry.data_buffer
        slot.target_global = entry.target_global
        slot.num_bytes = entry.num_bytes
        slot.write_once = entry.write_once
    signal_list = CSignalList(
        ctypes.cast(array, ctypes.POINTER(CSignalMapping)), len(entries)
    )
    return (signal_list, array)


class SnmulationRunner:
    """Builds and loads the generic C simulation runner.

    The runner is a tiny shared library compiled from ``sim_interface.c``.
    It is built once, cached in the user cache directory, and reused;
    """

    def __init__(self, library: ctypes.CDLL):
        self._library = library
        # INFO: hard coded mapping to 'sim_interface.c'
        self._run_global_simulation = library.run_global_simulation
        self._run_global_simulation.argtypes = [
            ctypes.POINTER(GFUNCTYPE),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(CSignalList),
            ctypes.POINTER(CSignalList),
            PROGRESS_CB,
        ]
        self._run_global_simulation.restype = ctypes.c_int

    @staticmethod
    def _source_path() -> Path:
        return Path(__file__).with_name("sim_interface.c")

    @classmethod
    def _cached_library_path(cls, sharedlibpath: Path) -> Path:
        digest = bin_based_hash(sharedlibpath)[
            :16
        ]  # magic numer: 16 to keep filename somewhat short
        return cls._cache_dir() / f"sim_interface-{digest}{cls._library_suffix()}"

    @staticmethod
    @safely_run(
        default_return=None,
        exception_msg="Loading sim_interface.c library failed.",
        log=logger,
    )
    def _load(path: Path) -> ctypes.CDLL | None:
        return ctypes.CDLL(str(path))

    @classmethod
    # TODO: check how to implement safely_run here without creating crap on the harddrive
    # @safely_run(
    #     default_return=False,
    #     exception_msg="Compiling the sim_interface.c failed.",
    #     log=logger,
    # )
    def _compile(cls, out_path: Path, source: Path) -> bool:
        compiler = cls._compiler()
        if compiler is None:
            logger.warning(
                "No C compiler found to build the simulation runner (tried %s).",
                ", ".join(
                    [os.environ.get(COMPILER_ENV)] + list(COMPILER_CANDIDATES)
                    if os.environ.get(COMPILER_ENV)
                    else COMPILER_CANDIDATES
                ),
            )
            return False

        if os.name == "nt":  # windows
            flags = ["-shared", "-O2"]
        else:  # linux
            flags = ["-shared", "-fPIC", "-O2"]

        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = out_path.with_name(f"{out_path.name}.tmp{os.getpid()}")
        command = [compiler, *flags, "-o", str(tmp_path), str(source)]
        try:
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
        except (subprocess.CalledProcessError, OSError) as e:
            logger.warning("Compiling the simulation runner failed: %s", e)
            tmp_path.unlink(missing_ok=True)
            return False
        tmp_path.replace(out_path)
        return True

    @classmethod
    def load(cls) -> "SimulationRunner | None":
        """Build, load the 'SimulationRunner' library (sim_interface.c compiled).

        The behaviour can be adapted via the environment variable 'ARES_SIM_RUNNER':
            - 'python': python loop is used (no compiler necessary)
            - 'crunner': c-library is created and used.

        Returns:
            A ready-to-use :class:`SimulationRunner`, or ``None`` when the
            Python stepping loop should be used instead.
        """
        override = os.environ.get(OVERRIDE_ENV, "").strip().lower()
        force_python = override == "python"
        force_crunner = override == "crunner"

        if force_python:
            logger.debug("ARES_SIM_RUNNER=python: using the Python loop.")
            return None

        source = cls._source_path()
        if not source.exists():
            logger.debug("sim_interface.c not found: using the Python loop.")
            return None

        cached = cls._cached_library_path(source)
        library = cls._load(cached)
        if library is None and cls._compile(cached, source):
            library = cls._load(cached)
        if library is None:
            if force_crunner:
                logger.error(
                    "ARES_SIM_RUNNER=runner but the simulation runner could not "
                    f"be built from '{source}'."
                )
                raise
            logger.warning(
                "C simulation runner unavailable; falling back to the Python loop."
            )
            return None

        logger.info("C simulation runner loaded from '%s'.", cached)
        return cls(library)

    def run(
        self,
        functions: object,
        num_functions: int,
        sim_steps: int,
        input_list: CSignalList | None,
        output_list: CSignalList | None,
        progress_cb: Callable[[int], None] | None = None,
    ) -> int:
        """Execute the simulation in C.

        Args:
            functions: ctypes array of ``GlobalSimFunc`` entries (the cyclical
                simulation functions) which must outlive this call.
            num_functions: Number of entries in ``functions``.
            sim_steps: Number of time steps to simulate.
            input_list: Input signal mappings, or ``None`` for no inputs.
            output_list: Output signal mappings, or ``None`` for no outputs.
            progress_cb: Optional callback fired at the 10% boundaries of the
                step range.

        Returns:
            The runner's return code (0 :success, 1: fail).
        """
        return self._run_global_simulation(
            functions,
            num_functions,
            sim_steps,
            ctypes.byref(input_list) if input_list is not None else None,
            ctypes.byref(output_list) if output_list is not None else None,
            progress_cb,
        )

    @staticmethod
    def _library_suffix() -> str:
        if os.name == "nt":
            return ".dll"
        return ".so"

    @staticmethod
    def _cache_dir() -> Path:
        override = os.environ.get(CACHE_ENV)
        if override:
            return Path(override).expanduser()
        if os.name == "nt":
            base = Path(
                os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
            )
        else:
            base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        return base / "ares"

    @staticmethod
    def _compiler() -> str | None:
        candidates = []
        configured = os.environ.get(COMPILER_ENV)
        if configured:
            candidates.append(configured)
        candidates.extend(COMPILER_CANDIDATES)
        for candidate in candidates:
            compiler_path = shutil.which(candidate)
            if compiler_path:
                return compiler_path
        return None
