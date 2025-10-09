#include "inout_handling.h"
#include <stdint.h>

int32_t parameter_scalar = 0;
uint32_t parameter_array1d[3] = {0};
float parameter_array2d[2][3] = {{0}};

int32_t signal_scalar = 0;
uint32_t signal_array1d[3] = {0};
float signal_array2d[2][3] = {{0}};

void ares_simunit()
{
    inout_handling(
        &parameter_scalar,
        parameter_array1d,
        parameter_array2d,
        &signal_scalar,
        signal_array1d,
        signal_array2d
    );
}
