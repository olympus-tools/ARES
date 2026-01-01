# examples/sim_unit/Makefile
# commands:
#   - make derivation
#   - make lowpassfilterfirstorder
#   - make inout-handling
#   - make clean

SHELL := /bin/sh

CC      ?= gcc
CFLAGS  ?= -shared -fPIC
RM      ?= rm -f

.PHONY: all
all: derivation lowpassfilterfirstorder inout-handling

.PHONY: derivation
derivation:
	@echo "Compiling sim_unit \"derivation\"..."
	$(CC) $(CFLAGS) -o derivation/derivation.so derivation/wrapper.c derivation/derivation.c

.PHONY: lowpassfilterfirstorder
lowpassfilterfirstorder:
	@echo "Compiling sim_unit \"lowpassfilterfirstorder\"..."
	$(CC) $(CFLAGS) -o lowpassfilterfirstorder/lowpassfilterfirstorder.so lowpassfilterfirstorder/wrapper.c lowpassfilterfirstorder/lowpassfilterfirstorder.c

.PHONY: inout-handling
inout-handling:
	@echo "Compiling sim_unit \"inout_handling\"..."
	$(CC) $(CFLAGS) -o inout_handling/inout_handling.so inout_handling/wrapper.c inout_handling/inout_handling.c

.PHONY: clean
clean:
	@echo "Cleaning sim_unit files..."
	$(RM) inout_handling/*.so
	$(RM) derivation/*.so
	$(RM) lowpassfilterfirstorder/*.so
