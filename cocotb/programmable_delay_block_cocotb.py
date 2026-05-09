"Author chatgpt 5.3 codex"
"needs to be studied"
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

UNIT = "ns"
PERIOD = 10
TRACE_EVERY_TICK = True


def get_params(dut):
    """Read elaborated RTL parameters from DUT."""
    width = int(dut.ELEMENT_INPUT_WIDTH.value)
    depth = int(dut.DEPTH.value)
    height = int(dut.HEIGHT.value)
    sel_width = int(dut.SEL_DELAY_WIDTH.value)
    return width, depth, height, sel_width


def get_delay_stages(depth):
    return max(depth - 1, 1)


def mask(width):
    return (1 << width) - 1


def fmt_lanes(lanes, width):
    hex_digits = max(1, (width + 3) // 4)
    return "[" + ", ".join(f"0x{value:0{hex_digits}X}" for value in lanes) + "]"


def fmt_lanes_decimal(lanes):
    return "[" + ", ".join(str(int(value)) for value in lanes) + "]"


def format_matrix_rows_decimal(matrix, row_label_prefix=None):
    rows = []
    for idx, row in enumerate(matrix):
        row_text = fmt_lanes_decimal(row)
        if row_label_prefix is None:
            rows.append(row_text)
        else:
            rows.append(f"{row_label_prefix}{idx:03d}: {row_text}")
    return rows


def format_matrices_side_by_side_rows(named_mats, separator="  ", row_label_prefix="c"):
    blocks = []
    widths = []

    for name, mat in named_mats:
        lane_count = len(mat[0]) if mat else 0
        lane_header = f"lanes: {fmt_lanes_decimal(list(range(lane_count)))}"
        lines = [name, lane_header] + format_matrix_rows_decimal(mat, row_label_prefix)
        width = max(len(line) for line in lines) if lines else len(name)
        blocks.append(lines)
        widths.append(width)

    max_height = max((len(block) for block in blocks), default=0)
    padded_blocks = []
    for block, width in zip(blocks, widths):
        padded = block + [""] * (max_height - len(block))
        padded_blocks.append([line.ljust(width) for line in padded])

    rows = []
    for i in range(max_height):
        rows.append(separator.join(block[i] for block in padded_blocks))

    return "\n".join(rows)


def pack_lanes(lanes, lane_width):
    packed = 0
    for idx, value in enumerate(lanes):
        packed |= (value & mask(lane_width)) << (idx * lane_width)
    return packed


def unpack_lanes(packed, lane_width, height):
    lane_mask = mask(lane_width)
    lanes = []
    for idx in range(height):
        lanes.append((packed >> (idx * lane_width)) & lane_mask)
    return lanes


async def tick(dut):
    await RisingEdge(dut.clk)
    await Timer(1, unit=UNIT)


def log_tick_trace(dut, cycle, d_lanes, en_lanes, sel_lanes, q_lanes, state, width, depth):
    if not TRACE_EVERY_TICK:
        return

    lines = [
        f"--- Tick {cycle:03d} ---",
        f"D   : {fmt_lanes(d_lanes, width)}",
        f"EN  : {en_lanes}",
        f"SEL : {sel_lanes}",
        f"Q   : {fmt_lanes(q_lanes, width)}",
        "Delay stages per lane:",
    ]

    for lane_idx, lane_state in enumerate(state):
        stage_text = ", ".join(
            f"s{stage_idx}={value:#0{max(3, (width + 3) // 4 + 2)}x}"
            for stage_idx, value in enumerate(lane_state)
        )
        lines.append(f"  lane{lane_idx}: {stage_text}")

    dut._log.info("\n".join(lines))


def log_tick_trace_decimal(dut, cycle, d_lanes, en_lanes, sel_lanes, q_lanes, state, width, depth):
    if not TRACE_EVERY_TICK:
        return

    lines = [
        f"--- Tick {cycle:03d} ---",
        f"D   : {fmt_lanes_decimal(d_lanes)}",
        f"EN  : {en_lanes}",
        f"SEL : {sel_lanes}",
        f"Q   : {fmt_lanes_decimal(q_lanes)}",
        "Delay stages per lane:",
    ]

    for lane_idx, lane_state in enumerate(state):
        stage_text = ", ".join(
            f"s{stage_idx}={int(value)}" for stage_idx, value in enumerate(lane_state)
        )
        lines.append(f"  lane{lane_idx}: {stage_text}")

    dut._log.info("\n".join(lines))


def model_step(state, d_lanes, sel_lanes, en_lanes, width, delay_stages, height):
    """Reference model for one cycle sampled just after the rising edge."""
    next_state = [row[:] for row in state]
    for lane in range(height):
        if en_lanes[lane]:
            next_state[lane][0] = d_lanes[lane] & mask(width)
            for delay in range(1, delay_stages):
                next_state[lane][delay] = state[lane][delay - 1] & mask(width)

    # The test samples Q after the clock edge, so delayed selections must use next_state.
    q_lanes = [0] * height
    for lane in range(height):
        if sel_lanes[lane] == 0:
            q_lanes[lane] = d_lanes[lane] & mask(width)
        elif 0 < sel_lanes[lane] <= delay_stages:
            q_lanes[lane] = next_state[lane][sel_lanes[lane] - 1] & mask(width)
        else:
            q_lanes[lane] = 0

    return next_state, q_lanes


async def initialize_pipeline(dut, width, depth, height, sel_width):
    """Drive zeros to make internal delay memory deterministic."""
    delay_stages = get_delay_stages(depth)
    zeros_d = [0] * height
    zeros_sel = [0] * height
    ones_en = [1] * height

    dut.enable.value = pack_lanes(ones_en, 1)
    dut.sel_delay.value = pack_lanes(zeros_sel, sel_width)
    dut.D.value = pack_lanes(zeros_d, width)

    for _ in range(delay_stages + 1):
        await tick(dut)


async def run_sequence(dut, width, depth, height, sel_width, cycles, seed):
    """Run random traffic and compare DUT against reference each cycle."""
    rng = random.Random(seed)
    delay_stages = get_delay_stages(depth)
    state = [[0 for _ in range(delay_stages)] for _ in range(height)]
    sel_space = 1 << sel_width
    has_out_of_range = delay_stages < sel_space - 1

    for cycle in range(cycles):
        d_lanes = [rng.randrange(0, 1 << width) for _ in range(height)]
        en_lanes = [rng.randrange(0, 2) for _ in range(height)]

        sel_lanes = []
        for _ in range(height):
            # Mix valid and intentionally out-of-range delay selections when possible.
            if has_out_of_range and rng.random() >= 0.8:
                sel_lanes.append(rng.randrange(delay_stages + 1, sel_space))
            else:
                sel_lanes.append(rng.randrange(0, delay_stages + 1))

        expected_state, expected_q_lanes = model_step(
            state,
            d_lanes,
            sel_lanes,
            en_lanes,
            width,
            delay_stages,
            height,
        )

        dut.D.value = pack_lanes(d_lanes, width)
        dut.enable.value = pack_lanes(en_lanes, 1)
        dut.sel_delay.value = pack_lanes(sel_lanes, sel_width)

        await tick(dut)

        actual_q_lanes = unpack_lanes(int(dut.Q.value), width, height)
        log_tick_trace(
            dut,
            cycle=cycle,
            d_lanes=d_lanes,
            en_lanes=en_lanes,
            sel_lanes=sel_lanes,
            q_lanes=actual_q_lanes,
            state=expected_state,
            width=width,
            depth=delay_stages,
        )
        assert actual_q_lanes == expected_q_lanes, (
            f"Cycle {cycle}: Q mismatch\n"
            f"  d={d_lanes}\n"
            f"  sel={sel_lanes}\n"
            f"  en={en_lanes}\n"
            f"  expected={expected_q_lanes}\n"
            f"  actual={actual_q_lanes}"
        )

        state = expected_state


@cocotb.test()
async def test_programmable_delay_block_directed(dut):
    """Directed checks for bypass, delayed output, disabled updates, and out-of-range select."""
    cocotb.start_soon(Clock(dut.clk, PERIOD, unit=UNIT).start())
    width, depth, height, sel_width = get_params(dut)

    delay_stages = get_delay_stages(depth)
    await initialize_pipeline(dut, width, depth, height, sel_width)

    # 1) Bypass check (sel=0): Q should equal D on every lane.
    d_lanes = [(idx + 1) & mask(width) for idx in range(height)]
    sel_lanes = [0] * height
    en_lanes = [1] * height
    dut.D.value = pack_lanes(d_lanes, width)
    dut.sel_delay.value = pack_lanes(sel_lanes, sel_width)
    dut.enable.value = pack_lanes(en_lanes, 1)
    await tick(dut)
    assert unpack_lanes(int(dut.Q.value), width, height) == d_lanes

    # 2) Fill lane 0 with known history while other lanes stay at 0.
    history = []
    for val in range(min(delay_stages, 6)):
        lanes = [0] * height
        lanes[0] = (val + 10) & mask(width)
        history.append(lanes[0])
        dut.D.value = pack_lanes(lanes, width)
        dut.enable.value = pack_lanes([1] + [0] * (height - 1), 1)
        dut.sel_delay.value = pack_lanes([0] * height, sel_width)
        await tick(dut)

    # Request a delayed sample from lane 0.
    requested_delay = min(delay_stages, 3)
    dut.D.value = 0
    dut.enable.value = 0
    sel = [0] * height
    sel[0] = requested_delay
    dut.sel_delay.value = pack_lanes(sel, sel_width)
    await tick(dut)

    actual = unpack_lanes(int(dut.Q.value), width, height)[0]
    expected = history[-1 - requested_delay]
    assert actual == expected, f"Delayed value mismatch: expected {expected}, got {actual}"

    # 3) Out-of-range select should force zero (only if representable by sel_width).
    if delay_stages < (1 << sel_width) - 1:
        sel = [0] * height
        sel[0] = delay_stages + 1
        dut.sel_delay.value = pack_lanes(sel, sel_width)
        await tick(dut)
        assert unpack_lanes(int(dut.Q.value), width, height)[0] == 0


@cocotb.test()
async def test_programmable_delay_block_random(dut):
    """Randomized constrained test against software reference model."""
    cocotb.start_soon(Clock(dut.clk, PERIOD, unit=UNIT).start())
    width, depth, height, sel_width = get_params(dut)

    await initialize_pipeline(dut, width, depth, height, sel_width)
    await run_sequence(
        dut,
        width=width,
        depth=depth,
        height=height,
        sel_width=sel_width,
        cycles=200,
        seed=20260324,
    )


@cocotb.test()
async def test_programmable_delay_block_wave_form(dut):
    """Deterministic waveform-style test with fixed sel lanes and decimal logs."""
    cocotb.start_soon(Clock(dut.clk, PERIOD, unit=UNIT).start())
    width, depth, height, sel_width = get_params(dut)

    assert height == 8, "This test expects HEIGHT=8 so SEL can be [0..7]."
    delay_stages = get_delay_stages(depth)
    assert delay_stages >= 7, "This test expects DEPTH>=8 so SEL can be [0..7]."
    assert sel_width >= 3, "This test expects SEL_DELAY_WIDTH>=3 for values up to 7."
    assert (1 << width) > 10, "This test expects ELEMENT_INPUT_WIDTH wide enough for values > 10."

    await initialize_pipeline(dut, width, depth, height, sel_width)

    sel_lanes = list(range(8))
    en_lanes = [1] * height
    state = [[0 for _ in range(delay_stages)] for _ in range(height)]
    rng = random.Random(20260324)
    d_history = []
    q_history = []

    max_value = 1 << width
    assert max_value - 11 >= height, "Not enough unique values > 10 for all lanes."
    d_lanes = rng.sample(range(11, max_value), height)

    cycles = delay_stages + 4
    for cycle in range(cycles):
        expected_state, expected_q_lanes = model_step(
            state,
            d_lanes,
            sel_lanes,
            en_lanes,
            width,
            delay_stages,
            height,
        )

        dut.D.value = pack_lanes(d_lanes, width)
        dut.enable.value = pack_lanes(en_lanes, 1)
        dut.sel_delay.value = pack_lanes(sel_lanes, sel_width)

        await tick(dut)

        actual_q_lanes = unpack_lanes(int(dut.Q.value), width, height)
        d_history.append(d_lanes)
        q_history.append(actual_q_lanes)
        log_tick_trace_decimal(
            dut,
            cycle=cycle,
            d_lanes=d_lanes,
            en_lanes=en_lanes,
            sel_lanes=sel_lanes,
            q_lanes=actual_q_lanes,
            state=expected_state,
            width=width,
            depth=delay_stages,
        )
        assert actual_q_lanes == expected_q_lanes, (
            f"Cycle {cycle}: Q mismatch\n"
            f"  d={d_lanes}\n"
            f"  sel={sel_lanes}\n"
            f"  en={en_lanes}\n"
            f"  expected={expected_q_lanes}\n"
            f"  actual={actual_q_lanes}"
        )

        state = expected_state

    side_by_side = format_matrices_side_by_side_rows(
        [("D matrix", d_history), ("Q matrix", q_history)]
    )
    dut._log.info("D/Q matrices (cycles x lanes):\n%s", side_by_side)

