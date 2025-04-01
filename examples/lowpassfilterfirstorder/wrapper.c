#include "lowpassfilterfirstorder.h"

float input_value = 0.f;
float filter_output = 0.f;

void ares_simunit()
{
    filter_output = lowpassfilter_first_order(input_value);
}