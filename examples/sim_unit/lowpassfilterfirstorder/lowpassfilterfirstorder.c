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

#include "lowpassfilterfirstorder.h"

float filter_last_output = 0.f;
float cutoff_freq = 0.f;
float sample_time = 0.f;

/**
 * @brief First order low pass filter using cutoff frequency.
 *
 * @param[in] input_value Input signal to be filtered.
 * @return Current filter value.
 *
 * @note sample_time is expected in milliseconds and will be converted to seconds internally.
 */
float lowpassfilter_first_order(float input_value)
{
    // Convert sample_time from milliseconds to seconds
    float sample_time_s = sample_time / 1000.0f;

    // Calculate filter coefficient alpha from cutoff frequency and sample time
    float RC = 1.0f / (2.0f * 3.1415f * cutoff_freq);
    float alpha = sample_time_s / (RC + sample_time_s);

    filter_last_output = alpha * input_value + (1.0f - alpha) * filter_last_output;
    return filter_last_output;
}
