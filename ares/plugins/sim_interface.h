
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

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

// Simulation function pointer e.g. 'simunit'
typedef void (*GlobalSimFunc)(void);

// Progress callback to python instance, fired every 10%
typedef void (*ProgressCb)(int step_idx);

// TODO: update comment
/*
 * Struct connecting ARES data memory and a simulation unit input global.
 *
 * input:  `data_buffer` is the time-indexed input series;
 *         `target_global` receives its copy (ARES -> simulation unit).
 * output: `target_global` is copied back into the time-indexed `data_buffer`
 *          (simulation unit -> ARES)
 */
typedef struct {
    void *data_buffer;   // ARES buffer - AresSignal,
                         // consists of [(float) timestamps, (any) data]
    void *target_global; // address of the simulation unit's global data variable
    size_t num_bytes;    // bytes transferred per time step = bytesize + dimension
    bool write_once;     // copy once before the loop instead of every step (init-value)
} SignalMapping;

// Ordered list of signal mappings datatype.
typedef struct {
    SignalMapping *signals;
    int num_signals;
} SignalList;

/*
 * Runs `functions` provided via pointer for every time step 'sim_steps'.
 *
 * `write_once` inputs are copied into their globals once before the loop.
 * For every step: input row `i` is copied into each input global, every
 * function is called, then each output global is copied into output row `i`.
 * `progress`, when not NULL, is called at the 10%-of-range boundaries
 * (including step 0 and the final step).
 *
 * Returns 0 on success, non-zero when the arguments are invalid.
 */
int run_global_simulation(GlobalSimFunc *functions, int num_functions, int sim_steps,
                          SignalList *input, SignalList *output, ProgressCb progress);
