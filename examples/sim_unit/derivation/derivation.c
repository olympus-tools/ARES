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

#include "derivation.h"

float last_input_value = 0.f;
float sample_time = 0.f;

/**
 * @brief Calculates the numerical derivative of the input signal.
 *
 * @param[in] input_value Current input signal value.
 * @return Numerical derivative value.
 */
float derivation(float input_value)
{
    if (sample_time == 0.0f) {
        return 0.0f;
    }
    return (input_value - last_input_value) / sample_time;
}
