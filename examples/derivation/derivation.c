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