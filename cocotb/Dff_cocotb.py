import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.clock import Clock

@cocotb.test()
async def test_d_flipflop_basic(dut):
    """Test basic D flip-flop functionality"""
    
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize
    dut.D.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # Small delay after clock edge
    
    # Test 1: Set D=1 and check Q after clock edge
    dut.D.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.Q.value == 1, f"Expected Q=1, got Q={dut.Q.value}"
    dut._log.info("Test 1 passed: D=1 -> Q=1")
    
    # Test 2: Set D=0 and check Q after clock edge
    dut.D.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.Q.value == 0, f"Expected Q=0, got Q={dut.Q.value}"
    dut._log.info("Test 2 passed: D=0 -> Q=0")
    
    # Test 3: Verify Q holds value during low clock
    dut.D.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert dut.Q.value == 1, f"Expected Q=1, got Q={dut.Q.value}"
    
    # Change D while clock is low - Q should not change
    await FallingEdge(dut.clk)
    dut.D.value = 0
    await Timer(3, units="ns")  # Wait in the middle of low phase
    assert dut.Q.value == 1, f"Q changed when clock was low! Expected Q=1, got Q={dut.Q.value}"
    dut._log.info("Test 3 passed: Q holds value when clock is low")
    
    dut._log.info("All basic tests passed!")


@cocotb.test()
async def test_d_flipflop_sequence(dut):
    """Test D flip-flop with a sequence of values"""
    
    # Create a 10ns period clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Test sequence
    test_values = [0, 1, 1, 0, 1, 0, 0, 1]
    
    # Initialize
    dut.D.value = 0
    await RisingEdge(dut.clk)
    
    for i, value in enumerate(test_values):
        dut.D.value = value
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert dut.Q.value == value, f"Cycle {i}: Expected Q={value}, got Q={dut.Q.value}"
        dut._log.info(f"Cycle {i}: D={value} -> Q={dut.Q.value} ✓")
    
    dut._log.info(f"Sequence test passed! Tested {len(test_values)} values")


@cocotb.test()
async def test_d_flipflop_toggle(dut):
    """Test rapid toggling of D flip-flop"""
    
    # Create a 10ns period clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize
    dut.D.value = 0
    await RisingEdge(dut.clk)
    
    # Toggle D for multiple cycles
    for i in range(10):
        expected_value = i % 2
        dut.D.value = expected_value
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        assert dut.Q.value == expected_value, f"Toggle cycle {i}: Expected Q={expected_value}, got Q={dut.Q.value}"
    
    dut._log.info("Toggle test passed! D flip-flop toggled correctly for 10 cycles")
