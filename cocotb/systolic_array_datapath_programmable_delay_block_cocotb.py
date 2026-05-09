import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from test_utils import matrix

UNIT = "ns"
PERIOD = 10


def get_params(dut):
    height = int(dut.HEIGHT.value)
    width = int(dut.WIDTH.value)
    elem_w = int(dut.ELEMENT_INPUT_WIDTH.value)
    acc_w = int(dut.ACCUMULATOR_WIDTH.value)
    sel_w_a = int(dut.SEL_DELAY_WIDTH_A.value)
    sel_w_b = int(dut.SEL_DELAY_WIDTH_B.value)
    depth_a = int(dut.DEPTH_A.value)
    depth_b = int(dut.DEPTH_B.value)
    return height, width, elem_w, acc_w, sel_w_a, sel_w_b, depth_a, depth_b


def pack_unsigned(values, bit_width):
    packed = 0
    mask = (1 << bit_width) - 1
    for idx, value in enumerate(values):
        packed |= (int(value) & mask) << (idx * bit_width)
    return packed


def unpack_signed(packed, bit_width, count):
    out = []
    mask = (1 << bit_width) - 1
    sign = 1 << (bit_width - 1)
    for idx in range(count):
        raw = (packed >> (idx * bit_width)) & mask
        if raw & sign:
            raw -= 1 << bit_width
        out.append(raw)
    return out


async def tick(dut):
    await RisingEdge(dut.clk)
    await Timer(1, unit=UNIT)


def full_mask(width):
    return (1 << width) - 1


def wrap_signed(value, bit_width):
    raw = int(value) & full_mask(bit_width)
    sign = 1 << (bit_width - 1)
    if raw & sign:
        raw -= 1 << bit_width
    return raw


def wrap_matrix_signed(values, bit_width):
    wrapped = np.zeros_like(values, dtype=np.int32)
    for r in range(values.shape[0]):
        for c in range(values.shape[1]):
            wrapped[r, c] = wrap_signed(values[r, c], bit_width)
    return wrapped


def set_accumulate_mode(dut, height, width):
    pe_count = height * width
    dut.input_enable.value = full_mask(pe_count)
    dut.acc_enable.value = full_mask(pe_count)
    dut.sel_adder_mux.value = full_mask(pe_count)
    dut.sel_acc_mux.value = full_mask(pe_count)


def set_shift_down_mode(dut, height, width, propagate_inputs=False):
    pe_count = height * width
    dut.input_enable.value = full_mask(pe_count) if propagate_inputs else 0
    dut.acc_enable.value = full_mask(pe_count)
    dut.sel_adder_mux.value = 0
    dut.sel_acc_mux.value = 0


@cocotb.test()
async def test_matrix_multiply_with_input_delays(dut):
    (
        height,
        width,
        elem_w,
        acc_w,
        sel_w_a,
        sel_w_b,
        depth_a,
        depth_b,
    ) = get_params(dut)

    assert height == width, (
        "This test currently assumes square matrices; "
        f"got HEIGHT={height}, WIDTH={width}"
    )

    cocotb.start_soon(Clock(dut.clk, PERIOD, unit=UNIT).start())

    # Delay profile: lane i is delayed by i clocks.
    sel_a = [i for i in range(height)]
    sel_b = [i for i in range(width)]
    assert max(sel_a) < (1 << sel_w_a), "SEL_DELAY_WIDTH_A is too small for HEIGHT lanes"
    assert max(sel_b) < (1 << sel_w_b), "SEL_DELAY_WIDTH_B is too small for WIDTH lanes"
    dut.sel_delay_a.value = pack_unsigned(sel_a, sel_w_a)
    dut.sel_delay_b.value = pack_unsigned(sel_b, sel_w_b)
    dut.delay_enable_a.value = (1 << height) - 1
    dut.delay_enable_b.value = (1 << width) - 1

    # Clear accumulators and a/b forwarding registers with deterministic zeros.
    # This avoids unknown startup state in edge PEs polluting row 0 / col 0.
    dut.a_in.value = 0
    dut.b_in.value = 0
    set_shift_down_mode(dut, height, width, propagate_inputs=True)
    clear_cycles = max(depth_a, depth_b) + max(height, width) + 1
    for _ in range(clear_cycles):
        await tick(dut)

    # Generate signed matrices using helper utility.
    a_m = matrix(height, np.int8).matrix.astype(np.int32)
    b_m = matrix(width, np.int8).matrix.astype(np.int32)
    expected = wrap_matrix_signed(a_m @ b_m, acc_w)

    dut._log.info("A matrix:\n%s", a_m)
    dut._log.info("B matrix:\n%s", b_m)

    # Stream columns of A and rows of B, then pad with zeros to flush wavefront.
    set_accumulate_mode(dut, height, width)
    total_cycles = height + max(depth_a, depth_b) + height + width
    for t in range(total_cycles):
        if t < height:
            a_vec = [int(a_m[r, t]) for r in range(height)]
            b_vec = [int(b_m[t, c]) for c in range(width)]
        else:
            a_vec = [0] * height
            b_vec = [0] * width

        dut.a_in.value = pack_unsigned(a_vec, elem_w)
        dut.b_in.value = pack_unsigned(b_vec, elem_w)
        await tick(dut)

    # Capture full matrix results by reading bottom row then shifting down each cycle.
    got = np.zeros((height, width), dtype=np.int32)

    bottom = unpack_signed(int(dut.c_out.value), acc_w, width)
    got[height - 1, :] = bottom

    set_shift_down_mode(dut, height, width)
    dut.a_in.value = 0
    dut.b_in.value = 0
    for row in range(height - 2, -1, -1):
        await tick(dut)
        got[row, :] = unpack_signed(int(dut.c_out.value), acc_w, width)

    dut._log.info("Expected C:\n%s", expected)
    dut._log.info("Observed C:\n%s", got)

    if not np.array_equal(got, expected):
        diff = expected - got
        raise AssertionError(
            "Matrix multiplication mismatch\n"
            f"Expected:\n{expected}\n"
            f"Observed:\n{got}\n"
            f"Diff:\n{diff}"
        )
