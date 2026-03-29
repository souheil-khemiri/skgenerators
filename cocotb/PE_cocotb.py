import cocotb
import random
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.clock import Clock

unit = "ns"
period = 10
test = 0

#wait clock edge and some time for signals to propagate
async def clock_await(dut):
    await RisingEdge(dut.clk)
    await Timer(1, unit=unit)

#the following procedural functions are to set control inputs of the PE  to set the PE a specific state.
def standby_hold(dut):
    dut.input_row_enable.value=0
    dut.input_col_enable.value=0
    dut.acc_row_enable.value=0
    dut.acc_col_enable.value=0
    dut._log.info("standby-hold")

#multiplicaiton-hold functon/state
def multiply(dut):
    dut.input_row_enable.value=0
    dut.input_col_enable.value=0
    dut.acc_row_enable.value=1
    dut.acc_col_enable.value=1
    dut.sel_row_adder_mux.value=0
    dut.sel_col_adder_mux.value=0
    dut.sel_row_acc_mux.value=1
    dut.sel_col_acc_mux.value=1
    dut._log.info("multiplication-hold")

#start_new_mac functon/state
def multiply_stream(dut):
    dut.input_row_enable.value=1
    dut.input_col_enable.value=1
    dut.acc_row_enable.value=1
    dut.acc_col_enable.value=1
    dut.sel_row_adder_mux.value=0
    dut.sel_col_adder_mux.value=0
    dut.sel_row_acc_mux.value=1
    dut.sel_col_acc_mux.value=1
    dut._log.info("star_new_mac")

#shift_result 
def shift_result(dut):
    dut.input_row_enable.value=0
    dut.input_col_enable.value=0
    dut.acc_row_enable.value=1
    dut.acc_col_enable.value=1
    dut.sel_row_acc_mux.value=0
    dut.sel_col_acc_mux.value=0
    dut._log.info("shift_result")

#sift_result_input
def shift_result_input(dut):
    dut.input_row_enable.value=1
    dut.input_col_enable.value=1
    dut.acc_row_enable.value=1
    dut.acc_col_enable.value=1
    dut.sel_row_acc_mux.value=0
    dut.sel_col_acc_mux.value=0
    dut._log.info("shift_result_input")

#shift_input
def shift_input(dut):
    dut.input_row_enable.value=1
    dut.input_col_enable.value=1
    dut.acc_row_enable.value=0
    dut.acc_col_enable.value=0
    dut._log.info("shift_input")

# multiply and accumulate
def mac(dut):
    dut.input_row_enable.value=1
    dut.input_col_enable.value=1
    dut.acc_row_enable.value=1
    dut.acc_col_enable.value=1
    dut.sel_row_adder_mux.value=1
    dut.sel_col_adder_mux.value=1
    dut.sel_row_acc_mux.value=1
    dut.sel_col_acc_mux.value=1
    dut._log.info("mac")

#mac test script
async def mac_test_script(dut,clock):
    standby_hold(dut)
    await clock_await(dut)
    values1 = list(range(-128, 128))  # Signed 8-bit range
    values2 = list(range(-128, 128))    
    random.shuffle(values1)
    random.shuffle(values2)
    values1 = values1[:10]  # Test with a subset of values for brevity
    values2 = values2[:10]   
    multiply_stream(dut)  # Set to multiplication state to ensure we start with a known state before testing start_new_mac  
    maccumulation = 0
    mac_set = False
    for i,j in zip(values1, values2):
        dut.a_in.value = i
        dut.b_in.value = j
        await clock_await(dut)
        maccumulation += i * j
        # Model 16-bit signed overflow like hardware does
        if maccumulation > 32767:
            maccumulation = maccumulation - 65536
        elif maccumulation < -32768:
            maccumulation = maccumulation + 65536
        if mac_set == False:
            mac(dut)
            mac_set = True
        assert dut.c_out.value.to_signed() == maccumulation, f"Expected mac to be {maccumulation}, got {dut.c_out.value.to_signed()}"
        assert dut.a_in.value == dut.a_out.value , f"Explectd a_out to be equal to a_in={dut.a_in.value.to_signed()} got a_out ={dut.a_out.value.to_signed()}"
        assert dut.a_in.value == dut.a_out.value , f"Explectd b_out to be equal to b_in={dut.b_in.value.to_signed()} got b_out ={dut.b_out.value.to_signed()}"
        dut._log.info(f"maccumulation= {maccumulation}, c_out{dut.c_out.value.to_signed()}")
    standby_hold(dut)
    await clock_await(dut)
    assert dut.c_out.value.to_signed() == maccumulation, f"Expected mac to be {maccumulation}, got {dut.c_out.value.to_signed()}"
    for i in range(random.randint(10,20)):
        await clock_await(dut)
    assert dut.c_out.value.to_signed() == maccumulation, f"Expected mac to be {maccumulation}, got {dut.c_out.value.to_signed()}"
    dut._log.info(f"After random clocl cycles of accumulation stop maccumulation is: {maccumulation} and c_out is: {dut.c_out.value.to_signed()} ")
    



@cocotb.test()
async def standby_hold_test(dut):
    global test

    clock = Clock(dut.clk, period, unit=unit)
    cocotb.start_soon(clock.start())
    #capture initial output values (should be 'x' or 0 depending on simulator)
    initial_a = int(dut.a_out.value)
    initial_b = int(dut.b_out.value) 
    initial_c = int(dut.c_out.value)
    initial_accumulator = int(dut.accumulator_output.value)
    
    standby_hold(dut)
    
    #Test 1: Check outputs don't change when enable=0
    dut.a_in.value = random.randint(-128, 127)  # Signed 8-bit: -128 to 127
    dut.b_in.value = random.randint(-128, 127)  # Signed 8-bit: -128 to 127
    await clock_await(dut)
    
    # Verify outputs remained unchanged 
    assert int(dut.a_out.value) == initial_a, f"Expected a_out={initial_a} (unchanged), got a_out={dut.a_out.value}"
    assert int(dut.b_out.value) == initial_b, f"Expected b_out={initial_b} (unchanged), got b_out={dut.b_out.value}"
    assert int(dut.c_out.value) == initial_c, f"Expected c_out={initial_c} (unchanged), got c_out={dut.c_out.value}"
    assert int(dut.accumulator_output.value) == initial_accumulator, f"Initial accumulator_output={initial_accumulator} (unchanged), got accumulator_output={int(dut.accumulator_output.value)}"
    dut._log.info(f"Test {test} passed: Outputs unchanged when standby-hold (a_out={initial_a}, b_out={initial_b}, c_out={initial_c}), accumulator_output changed from {initial_accumulator} to {int(dut.accumulator_output.value)}")#
    test += 1
    for i in range(5):
        temp_a = int(dut.a_out.value)
        temp_b = int(dut.b_out.value)
        temp_c = int(dut.c_out.value)
        temp_acc = int(dut.accumulator_output.value)
        dut.a_in.value = random.randint(-128, 127)  # Signed 8-bit: -128 to 127
        dut.b_in.value = random.randint(-128, 127)  # Signed 8-bit: -128 to 127
        dut.c_in.value = random.randint(-32768,32767) # Signed 16-bit: -32768 to 32767

        await clock_await(dut)
        assert int(dut.a_out.value) == temp_a , f"Expected a_out={temp_a} (unchanged), got a_out={dut.a_out.value}"
        assert int(dut.b_out.value) == temp_b , f"Expected b_out={temp_b} (unchanged), got b_out={dut.b_out.value}"
        assert int(dut.c_out.value) == temp_c , f"Expected c_out={temp_c} (unchanged), got c_out={dut.c_out.value}"
        assert int(dut.accumulator_output.value) == temp_acc, f"Expected accumulator_output={temp_acc} (unchanged), got accumulator_output={int(dut.accumulator_output.value)}"
        dut._log.info(f"Test {test} passed: Outputs unchanged when standby-hold (a_out={temp_a}, b_out={temp_b}, c_out={int(temp_c)}), accumulator_output changed from {temp_acc} to {int(dut.accumulator_output.value)}")
    test += 1

@cocotb.test()
async def multiplication_test(dut):
    global test
    clock = Clock(dut.clk, period, unit=unit)
    cocotb.start_soon(clock.start())
    
    standby_hold(dut)
    await clock_await(dut)
    values1 = list(range(-128, 128))  # Signed 8-bit range
    values2 = list(range(-128, 128)) 
    random.shuffle(values1)
    random.shuffle(values2)
    set = False
    counter = 0
    for i,j in zip(values1, values2):
        counter += 1
        dut.a_in.value = i
        dut.b_in.value = j
        if set == False:
            multiply(dut)
            set = True
        await clock_await(dut)
        assert dut.c_out.value.to_signed() == i*j, f"Expected a={i} X b={j} to be {i*j}, got {int(dut.c_out.value)}"
        dut._log.info(f"multiplication nbr:{counter}. i={i}, a_in={dut.a_in.value.to_signed()}, j={j}, b_in={dut.b_in.value.to_signed()}, i x j={i*j}, c_out={dut.c_out.value.to_signed()}, accumulator_output={dut.accumulator_output.value.to_signed()}")
        dut._log.info(f"Test {test} passed: Multiplication for multiple inputs positive and negative is correct. No accumulation")
        test += 1
    #check a single multiplication persist
    temp_a = dut.a_in.value.to_signed()
    temp_b = dut.b_in.value.to_signed()
    for i in range (5): 
        await clock_await(dut)
    assert dut.a_in.value.to_signed() == temp_a, f"Expected a_in={temp_a} (unchanged), got a_out={dut.a_in.value.to_signed()}"
    assert dut.b_in.value.to_signed() == temp_b, f"Expected b_in={temp_b} (unchanged), got b_out={dut.a_in.value.to_signed()}"
    assert dut.c_out.value.to_signed() == temp_a*temp_b, f"Expected c_out={temp_a*temp_b} (unchanged), got c_out={dut.c_out.value.to_signed()}"
    dut._log.info(f"a_in= {dut.a_in.value.to_signed()}, temp_a= {temp_a}, b_in= {dut.b_in.value.to_signed()}, temp_b= {temp_b}, c_out= {dut.c_out.value.to_signed()} equals to temp_a*temp_b ={temp_a*temp_b} after 5 cycles, multiplication result is stable")
    
@cocotb.test()
async def mac_test(dut):
    global test 
    clock = Clock(dut.clk, period, unit=unit)
    cocotb.start_soon(clock.start())
    await mac_test_script(dut,clock)

@cocotb.test()
async def restart_mac_test(dut):
    global test
    clock = Clock(dut.clk, period, unit=unit)
    cocotb.start_soon(clock.start())
    await mac_test_script(dut,clock)
    dut._log.info("Restarting mac 1 done successfully")
    await mac_test_script(dut,clock)
    dut._log.info("Restarting mac 2 done successfully")
    await mac_test_script(dut,clock)
    dut._log.info("Restarting mac 3 done successfully")

@cocotb.test()
async def shift_input_test(dut):
    global test
    clock = Clock(dut.clk, period, unit=unit)
    cocotb.start_soon(clock.start())
    await mac_test_script(dut, clock)
    dut._log.info("did one mac")
    values1 = list(range(-128,128))
    values2 = list(range(-128,128))
    values3 = list(range(-128,128))
    random.shuffle(values1)
    random.shuffle(values2)
    random.shuffle(values3)
    shift_input_set = False
    for i in range(random.randint(15,60)): 
        if shift_input_set == False:
            shift_input(dut)
            shift_input_set = True
        dut.a_in.value = values1[i]
        dut.b_in.value = values2[i]
        await clock_await(dut)
        assert dut.a_out.value.to_signed() == dut.a_in.value.to_signed(), f"Expected a_out={values1[i]} (shifted input), got a_out={dut.a_out.value.to_signed()}"
        assert dut.b_out.value.to_signed() == dut.b_in.value.to_signed(), f"Expected b_out  ={values2[i]} (shifted input), got b_out={dut.b_out.value.to_signed()}"
        dut._log.info(f"a_in={dut.a_in.value.to_signed()}, a_out={dut.a_out.value.to_signed()}, b_in={dut.b_in.value.to_signed()}, b_out={dut.b_out.value.to_signed()}")


@cocotb.test()
async def shift_result_input_test(dut):
    global test
    clock = Clock(dut.clk, period, unit=unit)
    cocotb.start_soon(clock.start())
    await mac_test_script(dut, clock)
    dut._log.info("did one mac")
    values1 = list(range(-128,128))
    values2 = list(range(-128,128))
    values3 = list(range(-128,128))
    random.shuffle(values1)
    random.shuffle(values2)
    random.shuffle(values3)
    shift_input_result_set = False
    for i in range(random.randint(15,60)): 
        if shift_input_result_set == False:
            shift_result_input(dut)
            shift_input_result_set = True
        dut.a_in.value = values1[i]
        dut.b_in.value = values2[i]
        dut.c_in.value = values3[i]
        await clock_await(dut)
        assert dut.a_out.value.to_signed() == dut.a_in.value.to_signed(), f"Expected a_out={values1[i]} (shifted input), got a_out={dut.a_out.value.to_signed()}"
        assert dut.b_out.value.to_signed() == dut.b_in.value.to_signed(), f"Expected b_out  ={values2[i]} (shifted input), got b_out={dut.b_out.value.to_signed()}"
        assert dut.c_out.value.to_signed() == dut.c_in.value.to_signed(), f"Expected c_out  ={values3[i]} (shifted input), got c_out={dut.c_out.value.to_signed()}"
        dut._log.info(f"a_in={dut.a_in.value.to_signed()}, a_out={dut.a_out.value.to_signed()}, b_in={dut.b_in.value.to_signed()}, b_out={dut.b_out.value.to_signed()}, c_in={dut.c_in.value.to_signed()}, c_out={dut.c_out.value.to_signed()}")

@cocotb.test()
async def shift_result_test(dut):
    clock = Clock(dut.clk, period, unit=unit)
    cocotb.start_soon(clock.start())
    await mac_test_script(dut, clock)
    dut._log.info("did one mac")
    values1 = list(range(-128,128))
    values2 = list(range(-128,128))
    values3 = list(range(-128,128))
    random.shuffle(values1)
    random.shuffle(values2)
    random.shuffle(values3)
    shift_input_result_set = False
    for i in range(random.randint(15,60)): 
        if shift_input_result_set == False:
            shift_result(dut)
            shift_input_result_set = True
        dut.a_in.value = values1[i]
        dut.b_in.value = values2[i]
        dut.c_in.value = values3[i]
        await clock_await(dut)
        #these assertions may cause the test to fail if the last saved value in a or b machtes the randomly asigned value to a_in or b_im. Although enable is not active, but the assertion will be true and test fails.
        #or the problem can be fixed by execluding the next assigned value to a_in and b_in from the random list of values.
        #assert dut.a_out.value.to_signed() != dut.a_in.value.to_signed(), f"Expected a_out={values1[i]} (shifted input), got a_out={dut.a_out.value.to_signed()}"
        #assert dut.b_out.value.to_signed() != dut.b_in.value.to_signed(), f"Expected b_out  ={values2[i]} (shifted input), got b_out={dut.b_out.value.to_signed()}"
        assert dut.c_out.value.to_signed() == dut.c_in.value.to_signed(), f"Expected c_out  ={values3[i]} (shifted input), got c_out={dut.c_out.value.to_signed()}"
        dut._log.info(f"a_in={dut.a_in.value.to_signed()}, a_out={dut.a_out.value.to_signed()}, b_in={dut.b_in.value.to_signed()}, b_out={dut.b_out.value.to_signed()}, c_in={dut.c_in.value.to_signed()}, c_out={dut.c_out.value.to_signed()}")

@cocotb.test()
async def random_input_to_mac(dut):
    clock = Clock(dut.clk, period, unit=unit)
    cocotb.start_soon(clock.start())
    standby_hold(dut)
    await clock_await(dut)
    loopend = 100
    while loopend!= 0 :
        dut.input_row_enable.value= random.randint(0,1)
        dut.input_col_enable.value= random.randint(0,1)
        dut.acc_row_enable.value= random.randint(0,1)
        dut.acc_col_enable.value= random.randint(0,1)
        dut.a_in.value= random.randint(-128,128)
        dut.b_in.value= random.randint(-128,128)
        dut.sel_row_adder_mux.value= random.randint(0,1)
        dut.sel_col_adder_mux.value= random.randint(0,1)
        dut.sel_row_acc_mux.value= random.randint(0,1)
        dut.sel_col_acc_mux.value= random.randint(0,1)
        dut.c_in.value= random.randint(-128,128)
        await clock_await(dut)
        dut._log.info(f"input_row_enable={dut.input_row_enable.value}\n"
                      f"input_col_enable={dut.input_col_enable.value}\n"
                      f"acc_row_enable={dut.acc_row_enable.value}\n"
                      f"acc_col_enable={dut.acc_col_enable.value}\n"
                      f"a_in={dut.a_in.value.to_signed()}\n"
                      f"b_in={dut.b_in.value.to_signed()}\n"
                      f"sel_row_adder_mux={dut.sel_row_adder_mux.value}\n"
                      f"sel_col_adder_mux={dut.sel_col_adder_mux.value}\n"
                      f"sel_row_acc_mux={dut.sel_row_acc_mux.value}\n"
                      f"sel_col_acc_mux={dut.sel_col_acc_mux.value}\n"
                      f"c_in={dut.c_in.value.to_signed()}\n"
                      f"a_out={dut.a_out.value.to_signed()}\n"
                      f"b_out={dut.b_out.value.to_signed()}\n"
                      f"c_out={dut.c_out.value.to_signed()}\n"
                      f"accumulator_output={dut.accumulator_output.value.to_signed()}")
        loopend = random.randint(-500, 500)
    await mac_test_script(dut, clock)
    dut._log.info("mac successfully completed after random input test")
         
         