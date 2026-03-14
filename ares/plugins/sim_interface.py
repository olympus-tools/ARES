import ctypes


class SigType:
    UINT8 = 0
    INT8 = 1
    UINT16 = 2
    INT16 = 3
    UINT32 = 4
    INT32 = 5
    INT32 = 6
    FLOAT = 7
    DOUBLE = 8


class SignalMapping(ctypes.Structure):
    _fields_ = [
        ("data_buffer", ctypes.c_void_p),  # The NumPy array pointer
        ("target_global", ctypes.c_void_p),  # The DLL global address
        ("type_id", ctypes.c_int),  # What kind of data is it?
    ]


class SimInput(ctypes.Structure):
    _fields_ = [
        ("signals", ctypes.POINTER(SignalMapping)),
        ("num_signals", ctypes.c_int),
    ]


class SimOutput(SimInput):
    _fields_ = [
        ("signals", ctypes.POINTER(SignalMapping)),
        ("num_signals", ctypes.c_int),
    ]


sim_interface_lib = ctypes.CDLL("./sim_interface.dll")
simulation_lib = ctypes.CDLL("./test.dll")

global_sim_func = getattr(simulation_lib, "global_test_simfunction")
c_global_sim_func = ctypes.CFUNCTYPE(None)(global_sim_func)

# guess this is a loop
test_signal_address = ctypes.addressof(
    ctypes.c_double.in_dll(simulation_lib, "test_signal")
)

input_mapping_array = (SignalMapping * 5)()
# ... fill mapping_array[0] .. [4] with data

output_mapping_array = (SignalMapping * 2)()

# SimInput container
sim_input = SimInput(ctypes.cast(input_mapping_array, ctypes.POINTER(SignalMapping)), 5)
sim_output = SimOutput(
    ctypes.cast(input_mapping_array, ctypes.POINTER(SignalMapping)), 2
)

# Pass the function from logic.dll INTO the runner from runner.dll (10000 = sim-lenght defined by meas)
sim_interface_lib.run_global_simulation(
    c_sim_func, 10000, ctypes.byref(sim_input), ctypes.byref(sim_output)
)
