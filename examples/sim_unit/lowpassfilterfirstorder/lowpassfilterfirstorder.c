#include "lowpassfilterfirstorder.h"

float filter_last_output = 0.f;
float cutoff_freq = 0.f;
float sample_time = 0.f;

/**
 * @brief First order low pass filter using cutoff frequency.
 *
 * @param[in] input_value Input signal to be filtered.
 * @return Current filter value.
 */
float lowpassfilter_first_order(float input_value)
{
    // Calculate filter coefficient alpha from cutoff frequency and sample time
    float RC = 1.0f / (2.0f * 3.1415f * cutoff_freq);
    float alpha = sample_time / (RC + sample_time);

    filter_last_output = alpha * input_value + (1.0f - alpha) * filter_last_output;
    return filter_last_output;
}
