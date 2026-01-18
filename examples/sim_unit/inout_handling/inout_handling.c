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
#include <stdio.h>

/**
 * @brief Demonstrates in-place modification of scalar, 1D, and 2D array parameters and signals.
 *
 * This function increments various types of parameters and signals to demonstrate
 * handling of scalar values, 1D arrays, and 2D arrays in ARES simulations.
 *
 * @param[in,out] parameter_scalar      Scalar parameter (int32_t[1]), incremented by 1.
 * @param[in,out] parameter_array1d     1D parameter array (uint32_t[3]), each element incremented by 1, 2, 3.
 * @param[in,out] parameter_array2d     2D parameter array (float[2][3]), each element incremented by 1.0 to 6.0.
 * @param[in,out] signal_scalar         Scalar signal (int32_t[1]), incremented by 2.
 * @param[in,out] signal_array1d        1D signal array (uint32_t[3]), each element incremented by 2, 3, 4.
 * @param[in,out] signal_array2d        2D signal array (float[2][3]), each element incremented by 1.0 to 7.0.
 * @param[in,out] alt_signal_scalar     Alternative scalar signal (int32_t[1]), incremented by 1.
 * @param[in,out] alt_signal_array1d    Alternative 1D signal array (uint32_t[3]), each element incremented by 1, 2, 3.
 * @param[in,out] alt_signal_array2d    Alternative 2D signal array (float[2][3]), each element incremented by 1.0 to 6.0.
 */
void inout_handling(
	int32_t parameter_scalar[1],
	uint32_t parameter_array1d[3],
	float parameter_array2d[2][3],
	int32_t signal_scalar[1],
	uint32_t signal_array1d[4],
	float signal_array2d[2][3],
	int32_t alt_signal_scalar[1],
	uint32_t alt_signal_array1d[4],
	float alt_signal_array2d[2][3]
)
{
	parameter_scalar[0]+= 1u;
	parameter_array1d[0] += 1u;
	parameter_array1d[1] += 2u;
	parameter_array1d[2] += 3u;
	parameter_array2d[0][0] += 1.0f;
	parameter_array2d[0][1] += 2.0f;
	parameter_array2d[0][2] += 3.0f;
	parameter_array2d[1][0] += 4.0f;
	parameter_array2d[1][1] += 5.0f;
	parameter_array2d[1][2] += 6.0f;

	alt_signal_scalar[0] += 1u;
	alt_signal_array1d[0] += 1u;
	alt_signal_array1d[1] += 2u;
	alt_signal_array1d[2] += 3u;
	alt_signal_array2d[0][0] += 1.0f;
	alt_signal_array2d[0][1] += 2.0f;
	alt_signal_array2d[0][2] += 3.0f;
	alt_signal_array2d[1][0] += 4.0f;
	alt_signal_array2d[1][1] += 5.0f;
	alt_signal_array2d[1][2] += 6.0f;

	signal_scalar[0] += 2u;
	signal_array1d[0] += 2u;
	signal_array1d[1] += 3u;
	signal_array1d[2] += 4u;
	signal_array2d[0][0] += 1.0f;
	signal_array2d[0][1] += 3.0f;
	signal_array2d[0][2] += 4.0f;
	signal_array2d[1][0] += 5.0f;
	signal_array2d[1][1] += 6.0f;
	signal_array2d[1][2] += 7.0f;

}
