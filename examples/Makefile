# examples/Makefile
# Data interface examples
#   - make data_caching
#   - make data_convertion => TODO: currently just one data type supported
#   - make data_labelfilter
#   - make data_resampling
#   - make data_vstack
# Parameter interface examples
#   - make param_caching
#   - make param_convertion
#   - make param_labelfilter
# Plugin examples
#   - make plugin_manipulation
# Sim unit examples
#   - make simunit_dependencies
#   - make simunit_interface_alt
#   - make simunit_interface_alt_default
#   - make simunit_interface_alt_value
#   - make simunit_interface_std
#   - make simunit_vstack

VENV_DIR ?= ../.venv

# Platform detection for virtual environment binary path
ifeq ($(OS),Windows_NT)
	VENV_BIN := $(VENV_DIR)/Scripts
else
	VENV_BIN := $(VENV_DIR)/bin
endif

ARES ?= "$(VENV_BIN)/ares"
.PHONY: all
all: data_caching \
     data_labelfilter \
     data_resampling \
     data_vstack \
     param_caching \
     param_convertion \
     param_labelfilter \
     plugin_manipulation \
     simunit_dependencies \
     simunit_interface_alt \
     simunit_interface_alt_default \
     simunit_interface_alt_value \
     simunit_interface_std \
     simunit_vstack

.PHONY: data_caching
data_caching:
	@echo "Running data_caching example..."
	@$(ARES) pipeline \
		-wf workflow/data_interface/data_caching.wf.json \
		--output output/ \
		--log-level=10

# .PHONY: data_convertion
# data_convertion:
# 	@echo "Running data_convertion example..."
# 	@$(ARES) pipeline \
# 		-wf workflow/data_interface/data_convertion.wf.json \
# 		--output output/ \
# 		--log-level=10

.PHONY: data_labelfilter
data_labelfilter:
	@echo "Running data_labelfilter example..."
	@$(ARES) pipeline \
		-wf workflow/data_interface/data_labelfilter.wf.json \
		--output output/ \
		--log-level=10

.PHONY: data_resampling
data_resampling:
	@echo "Running data_resampling example..."
	@$(ARES) pipeline \
		-wf workflow/data_interface/data_resampling.wf.json \
		--output output/ \
		--log-level=10

.PHONY: data_vstack
data_vstack:
	@echo "Running data_vstack example..."
	@$(ARES) pipeline \
		-wf workflow/data_interface/data_vstack.wf.json \
		--output output/ \
		--log-level=10

.PHONY: param_caching
param_caching:
	@echo "Running param_caching example..."
	@$(ARES) pipeline \
		-wf workflow/parameter_interface/param_caching.wf.json \
		--output output/ \
		--log-level=10

.PHONY: param_convertion
param_convertion:
	@echo "Running param_convertion example..."
	@$(ARES) pipeline \
		-wf workflow/parameter_interface/param_convertion.wf.json \
		--output output/ \
		--log-level=10

.PHONY: param_labelfilter
param_labelfilter:
	@echo "Running param_labelfilter example..."
	@$(ARES) pipeline \
		-wf workflow/parameter_interface/param_labelfilter.wf.json \
		--output output/ \
		--log-level=10

.PHONY: plugin_manipulation
plugin_manipulation:
	@echo "Running plugin_manipulation example..."
	@$(ARES) pipeline \
		-wf workflow/plugin/plugin_manipulation.wf.json \
		--output output/ \
		--log-level=10

.PHONY: simunit_dependencies
simunit_dependencies:
	@echo "Running simunit_dependencies example..."
	$(MAKE) -C sim_unit derivation
	$(MAKE) -C sim_unit lowpassfilterfirstorder
	@$(ARES) pipeline \
		-wf workflow/sim_unit/simunit_dependencies.wf.json \
		--output output/ \
		--log-level=10

.PHONY: simunit_interface_alt
simunit_interface_alt:
	@echo "Running simunit_interface_alt example..."
	$(MAKE) -C sim_unit inout-handling
	@$(ARES) pipeline \
		-wf workflow/sim_unit/simunit_interface_alt.wf.json \
		--output output/ \
		--log-level=10

.PHONY: simunit_interface_alt_default
simunit_interface_alt_default:
	@echo "Running simunit_interface_alt_default example..."
	$(MAKE) -C sim_unit inout-handling
	@$(ARES) pipeline \
		-wf workflow/sim_unit/simunit_interface_alt_default.wf.json \
		--output output/ \
		--log-level=10

.PHONY: simunit_interface_alt_value
simunit_interface_alt_value:
	@echo "Running simunit_interface_alt_value example..."
	$(MAKE) -C sim_unit inout-handling
	@$(ARES) pipeline \
		-wf workflow/sim_unit/simunit_interface_alt_value.wf.json \
		--output output/ \
		--log-level=10

.PHONY: simunit_interface_std
simunit_interface_std:
	@echo "Running simunit_interface_std example..."
	$(MAKE) -C sim_unit inout-handling
	@$(ARES) pipeline \
		-wf workflow/sim_unit/simunit_interface_std.wf.json \
		--output output/ \
		--log-level=10

.PHONY: simunit_vstack
simunit_vstack:
	@echo "Running simunit_vstack example..."
	$(MAKE) -C sim_unit inout-handling
	@$(ARES) pipeline \
		-wf workflow/sim_unit/simunit_vstack.wf.json \
		--output output/ \
		--log-level=10
