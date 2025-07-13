#include "function1.h"

// Global simulation variable, incremented on each call to function1.
int global_simulation_variable1 = 3;
float filter_last_output = 0;

/**
 * @brief An example function that takes a float scalar,
 * a pointer to a float, and a float array.
 *
 * @param[in] fun1_scalar1_float A simple floating-point value.
 * @param[inout] fun1_pointer1_float A pointer to a floating-point value (array of size 1).
 * @param[inout] fun1_array1_float A floating-point array of size 4.
 * @return int Returns 1 to indicate success.
 */
int function1(float fun1_scalar1_float,
              float fun1_pointer1_float[1],
              float fun1_array1_float[4])
{
    global_simulation_variable1++;
    return 1;
}

/**
 * @brief A low pass filter first order as example function.
 *
 * @param[in] input_value Input signal, that should be filtered.
 * @param[in] filter_alpha Filter coefficient.
 * @return current filter value.
 */
float lowpass_first_order(float input_value,
                        float filter_alpha) 
{
    float current_output = filter_alpha * input_value + (1.0 - filter_alpha) * filter_last_output;
    filter_last_output = current_output;
    return current_output;
}