#ifndef FUNCTION1_H
#define FUNCTION1_H

extern int global_simulation_variable1;

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
              float fun1_array1_float[4]);

float lowpass_first_order(float input_value,
                        float filter_alpha);

#endif // FUNCTION1_H