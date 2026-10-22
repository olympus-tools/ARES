/*
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
*/

/*
 * Generic C simulation runner for ARES simulation units.
 *
 * ARES orchestrates embedded-style simulation units: plain C shared
 * libraries whose simulation functions read and write *global variables*.
 * A global is the unit's interface: ARES copies the next time step's
 * input values into the input globals, calls the simulation function(s),
 * then copies the output globals out into an output buffer.
 *
 * Stepping that loop in Python costs one interpreter round-trip per time
 * step and per signal. This library moves the entire loop into C so a
 * whole simulation runs inside a single ctypes call. The per-step data
 * transfer cannot be removed entirely - the simulation functions only know
 * their globals - but it becomes one memcpy per signal inside the loop.
 *
 * The copy model is deliberately type-agnostic: every mapping describes its
 * own byte width per time step (`num_bytes` = itemsize * element count), so
 * scalar, 1D, 2D, integer, float, bool and fixed-size multi-dimensional
 * signals are all handled by the same memcpy with no dtype switch.
 */

#include "sim_interface.h"

int run_global_simulation(GlobalSimFunc *functions, int num_functions, int sim_steps,
                          SignalList *input, SignalList *output, ProgressCb progress_callback) {
    // validate inputs
    if (functions == NULL || num_functions <= 0 || sim_steps <= 0 || input == NULL ||
        output == NULL || progress_callback == NULL) {
        return 1;
    }

    // TODO: do we need this?
    // write_once signals
    if (input != NULL) {
        for (int j = 0; j < input->num_signals; j++) {
            SignalMapping *m = &input->signals[j]; // get signal pointer
            (m->write_once && m->data_buffer != NULL &&
             m->target_global != NULL) { // validate signal data
                memcpy(m->target_global, m->data_buffer, m->num_bytes);
            }
        }
    }

    /* progress boundaries mirror the Python loop's rounding of k*(steps-1)/10 */
    // init progress bar array, 10% steps
    int boundaries[11] = {0};
    if (sim_steps > 1) {
        for (int k = 0; k <= 10; k++) {
            boundaries[k] = (int)((double)k * (sim_steps - 1) / 10.0f + 0.5f);
        }
    }

    // simulation loop
    int progress_idx = 0;
    for (int i = 0; i < sim_steps; i++) {
        // input copy loop | ares-input -> *.so/*.dll
        for (int j = 0; j < input->num_signals; j++) {
            SignalMapping *m = &input->signals[j];
            if (!m->write_once && m->data_buffer != NULL && m->target_global != NULL) {
                memcpy(m->target_global, (char *)m->data_buffer + (size_t)i * m->num_bytes,
                       m->num_bytes);
            }
        }

        // looping over all functions
        for (int n = 0; n < num_functions; n++) {
            functions[n]();
        }

        // output copy loop | *.so/*.dll -> ares-output
        for (int j = 0; j < output->num_signals; j++) {
            SignalMapping *m = &output->signals[j];
            if (m->data_buffer != NULL && m->target_global != NULL) {
                memcpy((char *)m->data_buffer + (size_t)i * m->num_bytes, m->target_global,
                       m->num_bytes);
            }
        }

        // progress callback |
        if (progress_idx <= 10 && boundaries[progress_idx]) {
            progress_callback(i);
        }
    }

    return 0;
}
