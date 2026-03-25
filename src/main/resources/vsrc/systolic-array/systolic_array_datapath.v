module systolic_array_datapath
#(
    parameter HEIGHT = 8,
    parameter WIDTH = 8,
    parameter ELEMENT_INPUT_WIDTH = 8,
    parameter ACCUMULATOR_WIDTH = 16 //must be 2x ELEMENT_INPUT_WIDTH 

)
(
    input  clk,
    input  [HEIGHT-1:0]input_row_enable,
    input  [WIDTH-1:0]input_col_enable,
    input  [HEIGHT-1:0]acc_row_enable, // enable signal for row
    input  [WIDTH-1:0]acc_col_enable, // enable signal for accumulator register
    input  [ELEMENT_INPUT_WIDTH*HEIGHT-1:0]a_in,//signed [ELEMENT_INPUT_WIDTH-1:0]a_in [HEIGHT-1:0] verilog does not support array for port declaration, so we need to flatten the array.
    input  [ELEMENT_INPUT_WIDTH*WIDTH-1:0]b_in,//signed [ELEMENT_INPUT_WIDTH-1:0]b_in [WIDTH-1:0] verilog does not support array for port declaration, so we need to flatten the array.
    input  [HEIGHT-1:0]sel_row_adder_mux, // 1: sel accumulator output, 0: sel zero
    input  [WIDTH-1:0]sel_col_adder_mux, // 1: sel accumulator output, 0: sel zero
    input  [HEIGHT-1:0]sel_row_acc_mux, // 1: sel adder output, 0: sel c_in
    input  [WIDTH-1:0]sel_col_acc_mux, // 1: sel adder output, 0: sel c_in
    //input  signed [ACCUMULATOR_WIDTH-1:0]c_in,
    //output reg signed [ELEMENT_INPUT_WIDTH-1:0]a_out,
    //output reg signed [ELEMENT_INPUT_WIDTH-1:0]b_out,
    output [ACCUMULATOR_WIDTH*WIDTH-1:0]c_out //signed [ACCUMULATOR_WIDTH-1:0]c_out[WIDTH-1:0] need to be flattened 
);
// Internal wires for connecting PEs
// [column][row] indexing: a flows horizontally (columns), b flows vertically (rows), c flows vertically
wire signed [ELEMENT_INPUT_WIDTH-1:0] a_wire [WIDTH-1:0][HEIGHT-1:0];  // Horizontal connections
wire signed [ELEMENT_INPUT_WIDTH-1:0] b_wire [WIDTH-1:0][HEIGHT-1:0];  // Vertical connections
wire signed [ACCUMULATOR_WIDTH-1:0] c_wire [WIDTH-1:0][HEIGHT-1:0];    // Vertical accumulator connections

genvar i;  // column index
genvar j;  // row index

generate
    for(i = 0; i < WIDTH; i = i + 1) begin : gen_col
        for(j = 0; j < HEIGHT; j = j + 1) begin : gen_row
            PE #(
                .ELEMENT_INPUT_WIDTH(ELEMENT_INPUT_WIDTH),
                .ACCUMULATOR_WIDTH(ACCUMULATOR_WIDTH)
            ) pe_inst (
                .clk(clk),
                .input_row_enable(input_row_enable[j]),
                .input_col_enable(input_col_enable[i]),
                .acc_row_enable(acc_row_enable[j]),
                .acc_col_enable(acc_col_enable[i]),
                
                // a_in: from left edge or from previous PE in row
                .a_in(i == 0 ? $signed(a_in[(j+1)*ELEMENT_INPUT_WIDTH-1 : j*ELEMENT_INPUT_WIDTH]): a_wire[i-1][j]),
                
                // b_in: from top edge or from previous PE in column
                .b_in(j == 0 ? $signed(b_in[(i+1)*ELEMENT_INPUT_WIDTH-1 : i*ELEMENT_INPUT_WIDTH]): b_wire[i][j-1]),
                
                .sel_row_adder_mux(sel_row_adder_mux[j]),
                .sel_col_adder_mux(sel_col_adder_mux[i]),

                .sel_row_acc_mux(sel_row_acc_mux[j]),
                .sel_col_acc_mux(sel_col_acc_mux[i]),
                
                // c_in: 0 for top row, otherwise from previous PE in column
                .c_in(j == 0 ? {ACCUMULATOR_WIDTH{1'b0}} : c_wire[i][j-1]),
                
                // Outputs
                .a_out(a_wire[i][j]),  // Rightmost column a_out left unconnected (OK for outputs)
                .b_out(b_wire[i][j]),  // Bottom row b_out left unconnected (OK for outputs)
                .c_out(c_wire[i][j])
            );
        end
    end
endgenerate

// Connect bottom row c_out to module output
generate
    for(i = 0; i < WIDTH; i = i + 1) begin : gen_output
        assign c_out[(i+1)*ACCUMULATOR_WIDTH-1 : i*ACCUMULATOR_WIDTH] = c_wire[i][HEIGHT-1];
    end
endgenerate

endmodule


