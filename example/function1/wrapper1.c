#include "function1.h"

float fun1_scalar1_float = 0.f;
float fun1_pointer1_float[1] = {0.f};
float fun1_array1_float[4] = {0.f};
float fun1_array2_float[1] = {0.f};

float filter_input = 0.f;
float filter_output = 0.f;

/**
 * @brief A wrapper function for simulation, which calls 'function1'.
 *
 * This function prepares the data for the call to 'function1'
 * and executes the call. Currently, fixed global variables are used.
 *
 * @return int Returns 0 to indicate the completion of the simulation.
 */

void ares_simunit()
{
    int fun1_err = function1(fun1_scalar1_float,
                            fun1_pointer1_float,
                            fun1_array1_float);

    float filter_output = lowpass_first_order(filter_input, 0.5f);
}