#include "derivation.h"

float input_value = 0.f;
float derivation_output = 0.f;


void ares_simunit()
{
    derivation_output =  derivation(input_value);
}