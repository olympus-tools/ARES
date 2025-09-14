# examples/sim_unit/Makefile
# commands:
#   - make derivation
#   - make lowpassfilterfirstorder
#   - make clean

SHELL := /bin/sh

CC      ?= gcc
CFLAGS  ?= -shared -fPIC
RM      ?= rm -f

.PHONY: all
all: derivation lowpassfilterfirstorder

.PHONY: derivation
derivation:
	@echo "Compiling sim_unit \"derivation\"..."
	$(CC) $(CFLAGS) -o derivation/derivation.so derivation/wrapper.c derivation/derivation.c

.PHONY: lowpassfilterfirstorder
lowpassfilterfirstorder:
	@echo "Compiling sim_unit \"lowpassfilterfirstorder\"..."
	$(CC) $(CFLAGS) -o lowpassfilterfirstorder/lowpassfilterfirstorder.so lowpassfilterfirstorder/wrapper.c lowpassfilterfirstorder/lowpassfilterfirstorder.c

.PHONY: clean
clean:
	@echo "Cleaning sim_unit files..."
	$(RM) derivation/*.so
	$(RM) lowpassfilterfirstorder/*.so
