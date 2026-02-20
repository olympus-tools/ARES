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

#include "inout_handling.h"
#include <stdio.h>

// parameter inputs
int32_t parameter_scalar[1] = {0};
uint32_t parameter_array1d[3] = {0u};
float parameter_array2d[2][3] = {{0.f}};

/**
 * @brief Demonstrates in-place modification of scalar, 1D, and 2D array parameters and signals.
 *
 * This function increments various types of parameters and signals to demonstrate
 * handling of scalar values, 1D arrays, and 2D arrays in ARES simulations.
 *
 * @param[in,out] parameter_scalar_output      Scalar parameter (int32_t[1]), incremented by 1.
 * @param[in,out] parameter_array1d_output     1D parameter array (uint32_t[3]), each element incremented by 1, 2, 3.
 * @param[in,out] parameter_array2d_output     2D parameter array (float[2][3]), each element incremented by 1.0 to 6.0.
 * @param[in,out] signal_scalar         Scalar signal (int32_t[1]), incremented by 2.
 * @param[in,out] signal_array1d        1D signal array (uint32_t[3]), each element incremented by 2, 3, 4.
 * @param[in,out] signal_array2d        2D signal array (float[2][3]), each element incremented by 1.0 to 7.0.
*/

void inout_handling(
	int32_t signal_scalar[1],
	uint32_t signal_array1d[4],
	float signal_array2d[2][3],
	int32_t parameter_scalar_output[1],
	uint32_t parameter_array1d_output[3],
	float parameter_array2d_output[2][3]
)
{
	parameter_scalar_output[0] = parameter_scalar[0];
	parameter_array1d_output[0] = parameter_array1d[0];
	parameter_array1d_output[1] = parameter_array1d[1];
	parameter_array1d_output[2] = parameter_array1d[2];
	parameter_array2d_output[0][0] = parameter_array2d[0][0];
	parameter_array2d_output[0][1] = parameter_array2d[0][1];
	parameter_array2d_output[0][2] = parameter_array2d[0][2];
	parameter_array2d_output[1][0] = parameter_array2d[1][0];
	parameter_array2d_output[1][1] = parameter_array2d[1][1];
	parameter_array2d_output[1][2] = parameter_array2d[1][2];

	signal_scalar[0] += 2u;
	signal_array1d[0] += 2u;
	signal_array1d[1] += 3u;
	signal_array1d[2] += 4u;
	signal_array1d[3] += 5u;
	signal_array2d[0][0] += 1.0f;
	signal_array2d[0][1] += 3.0f;
	signal_array2d[0][2] += 4.0f;
	signal_array2d[1][0] += 5.0f;
	signal_array2d[1][1] += 6.0f;
	signal_array2d[1][2] += 7.0f;

}

void init_func(float signal_scalar_init[1]){

	signal_scalar_init[0] = 3.1415f;

}
