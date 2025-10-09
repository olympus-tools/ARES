
#ifndef INOUT_HANDLING_H
#define INOUT_HANDLING_H

#include <stdint.h>

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
);

#endif // INOUT_HANDLING_H
