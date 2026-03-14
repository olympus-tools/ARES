#include <stdbool.h>
#include <stdint.h>

typedef enum {
  T_UINT8,
  T_INT8,
  T_UINT16,
  T_INT16,
  T_UINT32,
  T_INT32,
  T_FLOAT,
  T_DOUBLE
} type_id;

typedef void (*GlobalSimFunc)(void);
typedef struct {
  double *data_buffer;   // data from ARES
  double *target_buffer; // data from simulation function
  type_id datatype;

} SignalMapping;

typedef struct {
  SignalMapping *signals;
  int num_signals;
} SimInput;

typedef struct {
  SignalMapping *signals;
  int num_signals;
} SimOutput;

void copy_input(void *src, void *dst, int type_id, int step_idx) {
  switch (type_id) {
  case 0: // UINT8
    ((uint8_t *)dst)[0] = ((uint8_t *)src)[step_idx];
    break;
  case 1: // INT8
    ((int8_t *)dst)[0] = ((int8_t *)src)[step_idx];
    break;
  case 3: // UINT16
    ((uint16_t *)dst)[0] = ((uint16_t *)src)[step_idx];
    break;
    // ... and so on
  }
}

void copy_output(void *src, void *dst, int type_id, int step_idx) {
  switch (type_id) {
  case 0: // UINT8
    ((uint8_t *)dst)[step_idx] = ((uint8_t *)src)[0];
    break;
  case 1: // INT8
    ((int8_t *)dst)[step_idx] = ((int8_t *)src)[0];
    break;
  case 3: // UINT16
    ((uint16_t *)dst)[step_idx] = ((uint16_t *)src)[0];
    break;
    // ... and so on
  }
}

// standard c-interface for simulation
int run_global_simulation(GlobalSimFunc simulation_function, int sim_steps,
                          SimInput *input, SimOutput *output) {
  for (int i = 0; i < sim_steps; i++) {
    // map inputs
    for (int j = 0; j < input->num_signals; j++) {
      SignalMapping m = input->signals[j];
      copy_input(m.data_buffer, m.target_buffer, m.datatype, i);
    }
    // run simulation function
    simulation_function();

    // map outputs
    for (int j = 0; j < output->num_signals; j++) {
      SignalMapping m = output->signals[j];
      copy_output(m.target_buffer, m.data_buffer, m.datatype, i);
    }
  }
  return 0;
}

// TODO:
// implement run_stack_simulation()
// implement example
