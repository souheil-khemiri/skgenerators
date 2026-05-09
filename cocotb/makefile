# Makefile

# Add verilator from conda environment to PATH (for version detection)
#export PATH := /mnt/c/SourceCode-MasterThesis-MatMulRoCCAcceleratedRISCVSoC/tools/verilator_sim_env/bin:$(PATH)

# 1. Select your simulator (default is icarus)
SIM ?= verilator
TOPLEVEL_LANG ?= verilog
#verilog source path
VERILOG_DIR = ../src/main/resources/vsrc/systolic-array

# 2. List your source files (Verilog or SystemVerilog)
#VERILOG_SOURCES += D_flipflop.v


# Activate conda environment when running simulation commands
#SIM_CMD_PREFIX := conda run --no-capture-output -p /mnt/c/SourceCode-MasterThesis-MatMulRoCCAcceleratedRISCVSoC/tools/verilator_sim_env

# 3. TOPLEVEL is the name of the module in your Verilog file
#TOPLEVEL = d_flipflop

# 4. MODULE is the name of your Python test file (without the .py)
#MODULE = Dff_cocotb

# 5. Include the cocotb makefiles
include $(shell cocotb-config --makefiles)/Makefile.sim

# ============================================================================
# CUSTOM TARGETS - Run multiple designs from one Makefile
# ============================================================================
# The above configuration (lines 1-25) is the ORIGINAL approach:
#   - Sets default values for VERILOG_SOURCES, TOPLEVEL, MODULE
#   - Running plain "make" uses those defaults
#
# The targets below show an ALTERNATIVE approach:
#   - Define named targets for each design
#   - Run specific tests with "make test_dff" or "make test_pe"
#   - Each target overrides the default variables for that specific test
# ============================================================================

.PHONY: test_dff test_pe test_sa_dp test_sa_dp_delay

# Target: Test D Flip-Flop
# Usage: make test_dff
test_dff:
	@echo "Running D Flip-Flop test..."
	$(MAKE) VERILOG_SOURCES=$(VERILOG_DIR)/D_flipflop.v TOPLEVEL=d_flipflop MODULE=Dff_cocotb

# Target: Test PE module with 8-bit inputs, 16-bit accumulator
# Usage: make test_pe
test_pe:
	@echo "Running PE test (8-bit inputs, 16-bit accumulator)..."
	$(MAKE) VERILOG_SOURCES=$(VERILOG_DIR)/PE.v TOPLEVEL=PE MODULE=PE_cocotb \
		VERILOG_PARAMETERS="ELEMENT_INPUT_WIDTH=8 ACCUMULATOR_WIDTH=16"
#this is not the right way to pass parameters, this is gpt slop. find the correct way to do it.
# Verilator specific flags
# Set parameters using -G flag
#EXTRA_ARGS += -GWIDTH=8 -GINIT_VALUE=0


# Target: Test Rectangular MAC PE Systolic Array Datapath
# Usage: make test_sa_dp
test_sa_dp:
	@echo "Running Rectangular MAC PE Systolic Array Datapath test..."
	$(MAKE) VERILOG_SOURCES="$(VERILOG_DIR)/systolic_array_datapath.v  $(VERILOG_DIR)/PE.v"\
	 TOPLEVEL=rectangular_mac_pe_systolic_array_datapath\
	 MODULE=rectangular_mac_pe_systolic_array_datapath_cocotb

# Target: Test Systolic Array Datapath + Programmable Delay Blocks
# Usage: make test_sa_dp_delay
test_sa_dp_delay:
	@echo "Running Systolic Array Datapath with Programmable Delay Blocks test..."
	$(MAKE) VERILOG_SOURCES="$(VERILOG_DIR)/systolic_array_datapath_programmable_delay_block.v $(VERILOG_DIR)/systolic_array_datapath.v $(VERILOG_DIR)/programmable_delay_block.v $(VERILOG_DIR)/PE.v" \
	 TOPLEVEL=systolic_array_datapath_programmable_delay_block \
	 MODULE=systolic_array_datapath_programmable_delay_block_cocotb2

# Target:delay_block
test_delay_block:
	@echo "Running programmable delay block ..."
	$(MAKE) VERILOG_SOURCES=$(VERILOG_DIR)/programmable_delay_block.v  \
	TOPLEVEL=programmable_delay_block \
	MODULE=programmable_delay_block_cocotb
