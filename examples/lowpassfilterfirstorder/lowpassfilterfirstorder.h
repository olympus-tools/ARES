#ifndef LOWPASSFILTERFIRSTORDER_H
#define LOWPASSFILTERFIRSTORDER_H

#include <math.h>

/**
 * @brief First order low pass filter using cutoff frequency.
 *
 * @param[in] input_value Input signal to be filtered.
 * @return Current filter value.
 */
float lowpassfilter_first_order(float input_value);

#endif // LOWPASSFILTERFIRSTORDER_H