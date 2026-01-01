/*
 * ________________________________________________________________________
 * |                                                                      |
 * |               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
 * |              $$  __$$\ $$  __$$\ $$  _____|$$  __$$\                 |
 * |              $$ /  $$ |$$ |  $$ |$$ |      $$ /  \__|                |
 * |              $$$$$$$$ |$$$$$$$  |$$$$$\    \$$$$$$\                  |
 * |              $$  __$$ |$$  __$$< $$  __|    \____$$\                 |
 * |              $$ |  $$ |$$ |  $$ |$$ |      $$\   $$ |                |
 * |              $$ |  $$ |$$ |  $$ |$$$$$$$$\ \$$$$$$  |                |
 * |              \__|  \__|\__|  \__|\________| \______/                 |
 * |                                                                      |
 * |              Automated Rapid Embedded Simulation (c)                 |
 * |______________________________________________________________________|
 *
 * Copyright 2025 Andrä Carotta
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * For details, see: https://github.com/AndraeCarotta/ares#7-license
 */

#include "inout_handling.h"
#include <stdio.h>

/**
 * @brief Demonstrates in-place modification of scalar, 1D, and 2D array parameters and signals.
 *
 *
 * @param[in,out] parameter_scalar   Scalar parameter (int8_t[1]), incremented by 1.
 * @param[in,out] parameter_array1d  1D parameter array (uint8_t[3]), each element incremented by 1.
 * @param[in,out] parameter_array2d  2D parameter array (float[2][3]), each element incremented by 3.0.
 * @param[in,out] signal_scalar      Scalar signal (int8_t[1]), incremented by 2.
 * @param[in,out] signal_array1d     1D signal array (uint8_t[3]), each element incremented by 2.
 * @param[in,out] signal_array2d     2D signal array (float[2][3]), each element incremented by 4.0.
 */
void inout_handling(
	int32_t parameter_scalar[1],
	uint32_t parameter_array1d[3],
	float parameter_array2d[2][3],
	int32_t signal_scalar[1],
	uint32_t signal_array1d[3],
	float signal_array2d[2][3]
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

	signal_scalar[0] += 1u;
	signal_array1d[0] += 1u;
	signal_array1d[1] += 2u;
	signal_array1d[2] += 3u;
	signal_array2d[0][0] += 1.0f;
	signal_array2d[0][1] += 2.0f;
	signal_array2d[0][2] += 3.0f;
	signal_array2d[1][0] += 4.0f;
	signal_array2d[1][1] += 5.0f;
	signal_array2d[1][2] += 6.0f;

}
