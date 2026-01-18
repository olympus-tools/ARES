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
*/

#include "inout_handling.h"
#include <stdint.h>

int32_t parameter_scalar = 0;
uint32_t parameter_array1d[3] = {0};
float parameter_array2d[2][3] = {{0}};

int32_t signal_scalar = 0;
uint32_t signal_array1d[4] = {0};
float signal_array2d[2][3] = {{0}};

int32_t alt_signal_scalar = 0;
uint32_t alt_signal_array1d[4] = {0};
float alt_signal_array2d[2][3] = {{0}};

void ares_simunit_2()
{
    inout_handling(
        &parameter_scalar,
        parameter_array1d,
        parameter_array2d,
        &signal_scalar,
        signal_array1d,
        signal_array2d,
        &alt_signal_scalar,
        alt_signal_array1d,
        alt_signal_array2d
    );
}
