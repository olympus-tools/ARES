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
