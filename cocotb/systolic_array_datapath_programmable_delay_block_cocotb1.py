import cocotb
import numpy as np
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from test_utils import matrix
from systolic_array_control import compute_control_matrices

UNIT = "ns"
PERIOD = 10

def get_params(dut):
    HEIGHT = int(dut.HEIGHT.value)
    WIDTH = int(dut.WIDTH.value)
    ELEMENT_INPUT_WIDTH = int(dut.ELEMENT_INPUT_WIDTH.value)
    ACCUMULATOR_WIDTH = int(dut.ACCUMULATOR_WIDTH.value)
    SEL_DELAY_WIDTH_A = int(dut.SEL_DELAY_WIDTH_A.value)
    SEL_DELAY_WIDTH_B = int(dut.SEL_DELAY_WIDTH_B.value)
    DEPTH_A = int(dut.DEPTH_A.value)
    DEPTH_B = int(dut.DEPTH_B.value)
    return HEIGHT, WIDTH, ELEMENT_INPUT_WIDTH, ACCUMULATOR_WIDTH, SEL_DELAY_WIDTH_A, SEL_DELAY_WIDTH_B, DEPTH_A, DEPTH_B

async def awaitclok(dut):
    await RisingEdge(dut.clk)
    await Timer(1, unit=UNIT)

def full_mask(width):
    """Return a bit mask with the lowest ``width`` bits set to 1.

    This is a small helper used by packing and fixed-width conversion logic.
    It constructs a mask as ``(1 << width) - 1``.

    Args:
        width (int): Number of least-significant bits set to 1.

    Returns:
        int: Mask value.

    Examples:
        width=4 -> 0b1111 -> 15
        width=8 -> 0b11111111 -> 255
    """
    return (1 << width) - 1


def wrap_signed(value, bit_width):
    """Interpret ``value`` as a signed two's-complement integer of ``bit_width`` bits.

    The function first truncates ``value`` to ``bit_width`` bits, then converts
    that truncated representation to a signed Python integer.

    Args:
        value (int): Input integer (can be positive or negative).
        bit_width (int): Width of the target signed representation.

    Returns:
        int: Signed integer in the range
            ``[-2**(bit_width-1), 2**(bit_width-1)-1]``.

    Examples:
        value=200, bit_width=8 -> -56
        value=300, bit_width=8 -> 44
        value=-1,  bit_width=8 -> -1
    """
    raw = int(value) & full_mask(bit_width)
    sign = 1 << (bit_width - 1)
    if raw & sign:
        raw -= 1 << bit_width
    return raw


def wrap_matrix_signed(values, bit_width):
    """Apply fixed-width signed wrapping to every element of a matrix.

    This is a matrix-level helper that calls :func:`wrap_signed` element-by-
    element so software reference values follow hardware overflow behavior.

    Args:
        values (np.ndarray): Input matrix of integer-like values.
        bit_width (int): Width of signed two's-complement representation.

    Returns:
        np.ndarray: Matrix with same shape as ``values`` where each element is
            wrapped/interpreted as a signed ``bit_width`` value.

    Example:
        values=[[200, -1], [300, -300]], bit_width=8
        returns=[[-56, -1], [44, -44]]
    """
    wrapped = np.zeros_like(values, dtype=np.int32)
    for r in range(values.shape[0]):
        for c in range(values.shape[1]):
            wrapped[r, c] = wrap_signed(values[r, c], bit_width)
    return wrapped


def pack_unsigned(values, bit_width):
    """Pack lane values into one flattened unsigned integer bus.

    Lane ``idx`` occupies bit range
    ``[idx*bit_width : (idx+1)*bit_width-1]`` (lane 0 is the least-significant
    field). Each lane value is masked to ``bit_width`` bits before insertion.

    Args:
        values (Sequence[int]): Per-lane integers to pack.
        bit_width (int): Field width (in bits) of each lane.

    Returns:
        int: Flattened packed bus value.

    Example:
        values=[3, 5, 12], bit_width=4
        packed = 0xC53 (binary fields: 1100_0101_0011)
    """
    packed = 0
    mask = (1 << bit_width) - 1
    for idx, value in enumerate(values):
        packed |= (int(value) & mask) << (idx * bit_width)
    return packed


def pack_matrix_unsigned(values_2d, bit_width):
    """Flatten a 2D matrix in row-major order and pack it into one bus.

    The matrix is traversed row by row, left to right, and each element is
    inserted into a ``bit_width``-wide field. This is useful when a 2D matrix
    needs to be represented as one packed integer bus for cocotb or RTL.

    Args:
        values_2d (Sequence[Sequence[int]]): Matrix-like object with shape
            ``height x width``.
        bit_width (int): Bit width of each matrix element.

    Returns:
        int: Flattened packed bus value.

    Example:
        values_2d = [[1, 2], [3, 4]], bit_width = 4
        row-major flattening gives [1, 2, 3, 4]
        packed value becomes 0x4321
    """
    packed = 0
    mask = (1 << bit_width) - 1
    lane_idx = 0

    for row in values_2d:
        for value in row:
            packed |= (int(value) & mask) << (lane_idx * bit_width)
            lane_idx += 1

    return packed


def unpack_signed(packed, bit_width, count):
    """Unpack signed lane values from a flattened fixed-width integer bus.

    This reverses ``pack_unsigned`` field placement and interprets each field as
    signed two's-complement using ``bit_width`` bits.

    Args:
        packed (int): Flattened bus value containing consecutive lane fields.
        bit_width (int): Bit width of each lane field.
        count (int): Number of lanes to extract.

    Returns:
        list[int]: Extracted lane values as signed integers.

    Example:
        packed=0xC53, bit_width=4, count=3
        extracted raw fields are [3, 5, 12]
        signed output is [3, 5, -4]
    """
    out = []
    mask = (1 << bit_width) - 1
    sign = 1 << (bit_width - 1)
    for idx in range(count):
        raw = (packed >> (idx * bit_width)) & mask
        if raw & sign:
            raw -= 1 << bit_width
        out.append(raw)
    return out


def unpack_unsigned(packed, bit_width, count):
    """Unpack unsigned lane values from a flattened integer bus.

    This is the unsigned counterpart to :func:`unpack_signed`. It keeps each
    extracted field as a non-negative Python integer, which is what we want for
    1-bit control signals.

    Args:
        packed (int): Flattened bus value containing consecutive lane fields.
        bit_width (int): Bit width of each lane field.
        count (int): Number of lanes to extract.

    Returns:
        list[int]: Extracted lane values as unsigned integers.
    """
    out = []
    mask = (1 << bit_width) - 1
    for idx in range(count):
        raw = (packed >> (idx * bit_width)) & mask
        out.append(raw)
    return out


def unpack_matrix_unsigned(packed, height, width, bit_width):
    """Unpack a flattened bus into a 2D row-major matrix.

    The lane order matches :func:`pack_matrix_unsigned`: row by row, left to
    right.

    Args:
        packed (int): Flattened bus value.
        height (int): Matrix height.
        width (int): Matrix width.
        bit_width (int): Bit width of each matrix element.

    Returns:
        np.ndarray: Matrix of shape ``(height, width)`` with unsigned values.
    """
    values = unpack_unsigned(packed, bit_width, height * width)
    return np.array(values, dtype=np.int32).reshape(height, width)


def format_matrices_side_by_side(named_mats, separator="  "):
    """Format multiple matrices side by side for compact logging."""
    blocks = []
    widths = []

    for name, mat in named_mats:
        mat_str = np.array2string(mat, separator=" ")
        lines = [name] + mat_str.splitlines()
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


def display_control_values(dut, height, width):
    """Print the control buses as unpacked matrices.

    Returns the decoded matrices so the caller can inspect them or assert on
    them in a test.
    """
    input_enable = unpack_matrix_unsigned(int(dut.input_enable.value), height, width, 1)
    acc_enable = unpack_matrix_unsigned(int(dut.acc_enable.value), height, width, 1)
    sel_adder_mux = unpack_matrix_unsigned(int(dut.sel_adder_mux.value), height, width, 1)
    sel_acc_mux = unpack_matrix_unsigned(int(dut.sel_acc_mux.value), height, width, 1)

    control_display = format_matrices_side_by_side(
        [
            ("input_enable", input_enable),
            ("acc_enable", acc_enable),
            ("sel_adder_mux", sel_adder_mux),
            ("sel_acc_mux", sel_acc_mux),
        ]
    )
    dut._log.info("control buses:\n%s", control_display)

    return input_enable, acc_enable, sel_adder_mux, sel_acc_mux


def display_accumulator_values(dut, height, width, accumulator_width):
    """Print each PE accumulator as a signed height x width matrix.

    This reads the internal ``accumulator_output`` register from every PE in
    ``systolic_array_datapath_inst`` and converts it to a signed Python int so
    the matrix matches the hardware's two's-complement interpretation.

    Returns:
        np.ndarray: Signed accumulator matrix with shape ``(height, width)``.
    """
    accumulators = np.zeros((height, width), dtype=np.int32)

    for row in range(height):
        for col in range(width):
            pe = dut.systolic_array_datapath_inst.gen_row[row].gen_col[col].pe_inst
            accumulators[row, col] = wrap_signed(int(pe.accumulator_output.value), accumulator_width)

    dut._log.info("Accumulator outputs:\n%s", accumulators)
    return accumulators


def display_pe_input_values(dut, height, width, element_input_width):
    """Print the current ``a_in`` and ``b_in`` values for every PE.

    The values are read from each instantiated ``PE`` inside
    ``systolic_array_datapath_inst`` and arranged into two separate matrices,
    one for ``a_in`` and one for ``b_in``.

    Returns:
        tuple[np.ndarray, np.ndarray]: Signed ``a_in`` and ``b_in`` matrices.
    """
    a_values = np.zeros((height, width), dtype=np.int32)
    b_values = np.zeros((height, width), dtype=np.int32)

    for row in range(height):
        for col in range(width):
            pe = dut.systolic_array_datapath_inst.gen_row[row].gen_col[col].pe_inst
            a_values[row, col] = wrap_signed(int(pe.a_in.value), element_input_width)
            b_values[row, col] = wrap_signed(int(pe.b_in.value), element_input_width)

    dut._log.info("PE a_in values:\n%s", a_values)
    dut._log.info("PE b_in values:\n%s", b_values)
    return a_values, b_values


def display_pe_output_values(dut, height, width, element_input_width):
    """Print the current ``a_out`` and ``b_out`` values for every PE.

    The values are read from each instantiated ``PE`` inside
    ``systolic_array_datapath_inst`` and arranged into two separate matrices,
    one for ``a_out`` and one for ``b_out``.

    Returns:
        tuple[np.ndarray, np.ndarray]: Signed ``a_out`` and ``b_out`` matrices.
    """
    a_values = np.zeros((height, width), dtype=np.int32)
    b_values = np.zeros((height, width), dtype=np.int32)

    for row in range(height):
        for col in range(width):
            pe = dut.systolic_array_datapath_inst.gen_row[row].gen_col[col].pe_inst
            a_values[row, col] = wrap_signed(int(pe.a_out.value), element_input_width)
            b_values[row, col] = wrap_signed(int(pe.b_out.value), element_input_width)

    dut._log.info("PE a_out values:\n%s", a_values)
    dut._log.info("PE b_out values:\n%s", b_values)
    return a_values, b_values


def display_delay_block_outputs(dut, height, width, element_input_width):
    """Print delay-block outputs as a column (A) and a row (B).

    Returns:
        tuple[np.ndarray, np.ndarray]: A column vector (HEIGHT x 1) and a row
            vector (1 x WIDTH) with signed values.
    """
    a_packed = int(dut.programmable_delay_block_inst_a.Q.value)
    b_packed = int(dut.programmable_delay_block_inst_b.Q.value)

    a_values = unpack_signed(a_packed, element_input_width, height)
    b_values = unpack_signed(b_packed, element_input_width, width)

    a_column = np.array(a_values, dtype=np.int32).reshape(height, 1)
    b_row = np.array(b_values, dtype=np.int32).reshape(1, width)

    dut._log.info("Delay block A outputs (column):\n%s", a_column)
    dut._log.info("Delay block B outputs (row):\n%s", b_row)
    return a_column, b_row

def set_shift_down_mode(dut, HEIGHT, WIDTH):
    pe_count = HEIGHT * WIDTH
    dut.input_enable.value = 0
    dut.acc_enable.value = full_mask(pe_count)
    dut.sel_adder_mux.value = 0
    dut.sel_acc_mux.value = 0
    
def set_standby_hold_mode(dut,HEIGHT, WIDTH):
    pe_count = HEIGHT * WIDTH
    dut.input_enable.value = 0
    dut.acc_enable.value = 0
    #dut.sel_adder_mux.value = 0
    #dut.sel_acc_mux.value = 0

# def set_MAC_PE_mode(dut,HEIGHT, WIDTH,skew_diag_index):
#     pe_count = HEIGHT * WIDTH
#     matrix = np.zeros((HEIGHT,WIDTH),dtype=np.bool)
#     for k in range(skew_diag_index+1):
#         for i in range(HEIGHT):
#             for j in range(WIDTH):
#                 if i+j == k:
#                     matrix[i,j] = 1
        
#     dut.input_enable.value = pack_matrix_unsigned(matrix,1)
#     dut.acc_enable.value = pack_matrix_unsigned(matrix,1)
#     dut.sel_adder_mux.value = pack_matrix_unsigned(matrix,1)
#     dut.sel_acc_mux.value = pack_matrix_unsigned(matrix,1)
def set_acc_enable_MAC_mode(dut,HEIGHT, WIDTH,skew_diag_index):
    pe_count = HEIGHT * WIDTH
    matrix = np.zeros((HEIGHT,WIDTH),dtype=np.bool)
    for k in range(skew_diag_index+1):
        for i in range(HEIGHT):
            for j in range(WIDTH):
                if i+j == k:
                    matrix[i,j] = 1
        
    dut.acc_enable.value = pack_matrix_unsigned(matrix,1)

def set_input_enable_MAC_mode(dut,HEIGHT, WIDTH,skew_diag_index):
    pe_count = HEIGHT * WIDTH
    matrix = np.zeros((HEIGHT,WIDTH),dtype=np.bool)
    for k in range(skew_diag_index+1):
        for i in range(HEIGHT):
            for j in range(WIDTH):
                if i+j == k:
                    matrix[i,j] = 1
        
    dut.input_enable.value = pack_matrix_unsigned(matrix,1)

def set_sel_adder_mux_MAC_mode(dut,HEIGHT, WIDTH,skew_diag_index):
    pe_count = HEIGHT * WIDTH
    matrix = np.zeros((HEIGHT,WIDTH),dtype=np.bool)
    for k in range(skew_diag_index+1):
        for i in range(HEIGHT):
            for j in range(WIDTH):
                if i+j == k:
                    matrix[i,j] = 1
        
    dut.sel_adder_mux.value = pack_matrix_unsigned(matrix,1)    

def set_sel_acc_mux_MAC_mode(dut,HEIGHT, WIDTH,skew_diag_index):
    pe_count = HEIGHT * WIDTH
    matrix = np.zeros((HEIGHT,WIDTH),dtype=np.bool)
    for k in range(skew_diag_index+1):
        for i in range(HEIGHT):
            for j in range(WIDTH):
                if i+j == k:
                    matrix[i,j] = 1
        
    dut.sel_acc_mux.value = pack_matrix_unsigned(matrix,1)

def set_HOLD_PE_mode(dut,HEIGHT, WIDTH,skew_diag_index):
    pe_count = HEIGHT * WIDTH
    matrix = np.ones((HEIGHT,WIDTH),dtype=np.bool)
    for k in range(skew_diag_index+1):
        for i in range(HEIGHT):
            for j in range(WIDTH):
                if i+j == k:
                    matrix[i,j] = 0

    dut.input_enable.value = pack_matrix_unsigned(matrix,1)
    dut.acc_enable.value = pack_matrix_unsigned(matrix,1)
    


        
    

@cocotb.test()
async def test_matrix_multiply_with_input_delays(dut):
    HEIGHT, WIDTH, ELEMENT_INPUT_WIDTH, ACCUMULATOR_WIDTH, SEL_DELAY_WIDTH_A, SEL_DELAY_WIDTH_B, DEPTH_A, DEPTH_B= get_params(dut)
    
    clock = Clock(dut.clk, PERIOD, unit=UNIT)
    cocotb.start_soon(clock.start())

    # Delay profile: lane i is delayed by i clocks.
    sel_a = [i for i in range(HEIGHT)]
    sel_b = [i for i in range(WIDTH)]
    assert max(sel_a) < (1 << SEL_DELAY_WIDTH_A), "SEL_DELAY_WIDTH_A is too small for HEIGHT lanes"
    assert max(sel_b) < (1 << SEL_DELAY_WIDTH_B), "SEL_DELAY_WIDTH_B is too small for WIDTH lanes"
    dut.sel_delay_a.value = pack_unsigned(sel_a, SEL_DELAY_WIDTH_A)
    dut.sel_delay_b.value = pack_unsigned(sel_b, SEL_DELAY_WIDTH_B)
    dut.delay_enable_a.value = (1 << HEIGHT) - 1
    dut.delay_enable_b.value = (1 << WIDTH) - 1

    #init state
    set_standby_hold_mode(dut,HEIGHT, WIDTH)

    # Clear accumulators and a/b forwarding registers with deterministic zeros.
    # This avoids unknown startup state in edge PEs polluting row 0 / col 0.
    dut.a_in.value = 0
    dut.b_in.value = 0
    set_shift_down_mode(dut, HEIGHT, WIDTH)
    clear_cycles = max(DEPTH_A, DEPTH_B) + max(HEIGHT, WIDTH) + 1
    for _ in range(clear_cycles):
        await awaitclok(dut)

    # Generate signed matrices using helper utility.
    a_m = matrix(HEIGHT, np.int8).matrix.astype(np.int32)
    b_m = matrix(WIDTH, np.int8).matrix.astype(np.int32)
    expected = wrap_matrix_signed(a_m @ b_m, ACCUMULATOR_WIDTH)

    dut._log.info("A matrix:\n%s", a_m)
    dut._log.info("B matrix:\n%s", b_m)

    #multiply
    DIM = HEIGHT # square dim systolic array
    M = HEIGHT #matix has the same shape as systolic array
    CARD_SKEW_DIAG= 2*DIM-1
    TOTAL_CYCLES= M+4*DIM-2
    set_standby_hold_mode(dut,HEIGHT, WIDTH)
    await awaitclok(dut)
    dut._log.info("control values before start")
    display_control_values(dut, HEIGHT, WIDTH)
    for i in range(TOTAL_CYCLES):
        a_vec = [0] * HEIGHT
        b_vec = [0] * WIDTH
        if i<M :
            a_vec = [int(a_m[r, i]) for r in range(HEIGHT)]
            b_vec = [int(b_m[i, c]) for c in range(WIDTH)]
            dut.a_in.value = pack_unsigned(a_vec, ELEMENT_INPUT_WIDTH)  
            dut.b_in.value = pack_unsigned(b_vec, ELEMENT_INPUT_WIDTH)

        input_enable_m, acc_enable_m, sel_adder_m, sel_acc_m = compute_control_matrices(
            HEIGHT,
            WIDTH,
            i,
            M,
            sel_a,
            sel_b,
        )
        dut.input_enable.value = pack_matrix_unsigned(input_enable_m, 1)
        dut.acc_enable.value = pack_matrix_unsigned(acc_enable_m, 1)
        dut.sel_adder_mux.value = pack_matrix_unsigned(sel_adder_m, 1)
        dut.sel_acc_mux.value = pack_matrix_unsigned(sel_acc_m, 1)

        dut._log.info(f"*********************just BEFORE clock edge number:##{i}##*********************")
        #display_control_values(dut, HEIGHT, WIDTH)
        a_column = np.array(a_vec, dtype=np.int32).reshape(HEIGHT, 1)
        dut._log.info("a_vec (column):\n%s", a_column)
        dut._log.info(f"b_vec: {b_vec}")
        #display_pe_input_values(dut, HEIGHT, WIDTH, ELEMENT_INPUT_WIDTH)
        #display_accumulator_values(dut, HEIGHT, WIDTH, ACCUMULATOR_WIDTH)
        dut._log.info(f"*********************##{i}##*********************")
        await awaitclok(dut)
        dut._log.info(f"*********************just AFTER clock edge number:##{i}##*********************")
        display_control_values(dut, HEIGHT, WIDTH)
        display_delay_block_outputs(dut, HEIGHT, WIDTH, ELEMENT_INPUT_WIDTH)
        display_pe_input_values(dut, HEIGHT, WIDTH, ELEMENT_INPUT_WIDTH)
        display_pe_output_values(dut, HEIGHT, WIDTH, ELEMENT_INPUT_WIDTH)
        display_accumulator_values(dut, HEIGHT, WIDTH, ACCUMULATOR_WIDTH)
        dut._log.info(f"*********************##{i}##*********************")
    # Capture full matrix results by reading bottom row then shifting down each cycle.
    got = np.zeros((HEIGHT, WIDTH), dtype=np.int32)

    bottom = unpack_signed(int(dut.c_out.value), ACCUMULATOR_WIDTH, WIDTH)
    got[HEIGHT - 1, :] = bottom

    set_shift_down_mode(dut, HEIGHT, WIDTH)
    dut._log.info("shift down results")
    display_control_values(dut, HEIGHT, WIDTH)

    # dut.a_in.value = 0
    # dut.b_in.value = 0
    for row in range(HEIGHT - 2, -1, -1):
        await awaitclok(dut)
        got[row, :] = unpack_signed(int(dut.c_out.value), ACCUMULATOR_WIDTH, WIDTH)

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

