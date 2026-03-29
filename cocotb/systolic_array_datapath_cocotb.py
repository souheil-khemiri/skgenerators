import cocotb
import random
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from cocotb.clock import Clock
import numpy as np
unit = "ns"
period = 10
test = 0
HEIGHT = 0
WIDTH = 0
ELEMENT_INPUT_WIDTH = 0
ACCUMULATOR_WIDTH = 0
class marix:
    def __init__(self, size):
        self.matrix=matrix = np.random.randint(  -2**(ELEMENT_INPUT_WIDTH-1), 2**(ELEMENT_INPUT_WIDTH-1), size=(size,size), dtype=np.int8)
        self.counter = 0
        self.size=size
    def get_next_row(self):
        if self.counter < self.size:
            row = self.matrix[self.counter, :]
            self.counter += 1
            return row
        else:
            raise IndexError("No more rows available")
            



#this function to be called at the beginning of each cocotb test to declare
def parameters_init(dut): 
    global HEIGHT, WIDTH, ELEMENT_INPUT_WIDTH, ACCUMULATOR_WIDTH
    HEIGHT = dut.HEIGHT.value.to_signed()
    WIDTH = dut.WIDTH.value.to_signed()
    ELEMENT_INPUT_WIDTH = dut.ELEMENT_INPUT_WIDTH.value.to_signed()
    ACCUMULATOR_WIDTH = dut.ACCUMULATOR_WIDTH.value.to_signed()

def rndm_sqr_matix_gen(size):
    global HEIGHT, WIDTH, ELEMENT_INPUT_WIDTH, ACCUMULATOR_WIDTH
    matrix = np.random.randint(  -2**(ELEMENT_INPUT_WIDTH-1), 2**(ELEMENT_INPUT_WIDTH-1), size=(size, size), dtype=np.int8)
    return matrix
def rndm_sqr_matix_gen_output(matrix):
    return





#wait clock edge and some time for signals to propagate
async def clock_await(dut):
    await RisingEdge(dut.clk)
    await Timer(1, unit=unit)

def idle_hold(dut):
    #parameters_init(dut)
    dut.input_row_enable.value=0
    dut.input_col_enable.value=0
    dut.acc_row_enable.value=0
    dut.acc_col_enable.value=0
    dut._log.info("standby-hold")

async def random_input(dut):
    parameters_init(dut)
    for i in range(random.randint(20,50)):
        dut.input_row_enable.value= random.getrandbits(HEIGHT)
        dut.input_col_enable.value=random.getrandbits(WIDTH)
        dut.acc_row_enable.value=random.getrandbits(HEIGHT)
        dut.acc_col_enable.value=random.getrandbits(WIDTH)
        dut.sel_row_adder_mux.value=random.getrandbits(HEIGHT)
        dut.sel_col_adder_mux.value=random.getrandbits(WIDTH)
        dut.sel_row_acc_mux.value=random.getrandbits(HEIGHT)
        dut.sel_col_acc_mux.value=random.getrandbits(WIDTH)
        dut.a_in.value=random.getrandbits((ELEMENT_INPUT_WIDTH*HEIGHT))
        dut.b_in.value=random.getrandbits((ELEMENT_INPUT_WIDTH*WIDTH))
        await clock_await(dut)
        dut._log.info("random input")

@cocotb.test()
async def test_idle(dut):
    parameters_init(dut)
    dut._log.info(f"HEIGHT={HEIGHT}, WIDTH={WIDTH}, ELEMENT_INPUT_WIDTH={ELEMENT_INPUT_WIDTH}, ACCUMULATOR_WIDTH={ACCUMULATOR_WIDTH}")
    dut._log.info(f"HEIGHT TYPE IS ={type(HEIGHT)}, WIDTH TYPE IS ={type(WIDTH)}, ELEMENT_INPUT_WIDTH TYPE IS ={type(ELEMENT_INPUT_WIDTH)}, ACCUMULATOR_WIDTH TYPE IS ={type(ACCUMULATOR_WIDTH)}")
    clock = Clock(dut.clk, period, unit=unit)
    cocotb.start_soon(clock.start())
    await random_input(dut)
    idle_hold(dut)
    dut._log.info(f"HEIGHT={HEIGHT}, WIDTH={WIDTH}, ELEMENT_INPUT_WIDTH={ELEMENT_INPUT_WIDTH}, ACCUMULATOR_WIDTH={ACCUMULATOR_WIDTH}")
    assert True