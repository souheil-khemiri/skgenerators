module systolic_array_datapath
#(
    parameter HEIGHT = 8,
    parameter WIDTH = 8,
    parameter ELEMENT_INPUT_WIDTH = 8,
    parameter ACCUMULATOR_WIDTH = 16 //must be 2x ELEMENT_INPUT_WIDTH 

)
(
    input  clk,
    input  [HEIGHT*WIDTH-1:0]input_enable,
    input  [HEIGHT*WIDTH-1:0]acc_enable,
    input  [ELEMENT_INPUT_WIDTH*HEIGHT-1:0]a_in,//signed [ELEMENT_INPUT_WIDTH-1:0]a_in [HEIGHT-1:0] verilog does not support array for port declaration, so we need to flatten the array.
    input  [ELEMENT_INPUT_WIDTH*WIDTH-1:0]b_in,//signed [ELEMENT_INPUT_WIDTH-1:0]b_in [WIDTH-1:0] verilog does not support array for port declaration, so we need to flatten the array.
    input  [HEIGHT*WIDTH-1:0]sel_adder_mux, // 1: sel accumulator output, 0: sel zero
    input  [HEIGHT*WIDTH-1:0]sel_acc_mux, // 1: sel adder output, 0: sel c_in
    output [ACCUMULATOR_WIDTH*WIDTH-1:0]c_out //signed [ACCUMULATOR_WIDTH-1:0]c_out[WIDTH-1:0] need to be flattened 
);
// Internal wires for connecting PEs
// [row][column] indexing
wire signed [ELEMENT_INPUT_WIDTH-1:0] a_in_wire [0:HEIGHT-1];  
wire signed [ELEMENT_INPUT_WIDTH-1:0] b_in_wire [0:WIDTH-1];  
// wire signed [ACCUMULATOR_WIDTH-1:0] c_out_wire [0:WIDTH-1];
wire signed [ELEMENT_INPUT_WIDTH-1:0] a_wire [0:HEIGHT-1][0:WIDTH-1];
wire signed [ELEMENT_INPUT_WIDTH-1:0] b_wire [0:HEIGHT-1][0:WIDTH-1];
wire signed [ACCUMULATOR_WIDTH-1:0] c_wire [0:HEIGHT-1][0:WIDTH-1];
wire input_enable_wire [0:HEIGHT-1][0:WIDTH-1];
wire acc_enable_wire [0:HEIGHT-1][0:WIDTH-1];
wire sel_adder_mux_wire [0:HEIGHT-1][0:WIDTH-1];
wire sel_acc_mux_wire [0:HEIGHT-1][0:WIDTH-1];
 
genvar i;  
genvar j;

generate
    for(i=0; i<HEIGHT; i=i+1)begin 
        assign a_in_wire[i] = a_in[i*ELEMENT_INPUT_WIDTH +: ELEMENT_INPUT_WIDTH];
        for(j=0; j<WIDTH; j=j+1)begin 
            assign input_enable_wire[i][j] = input_enable[i*WIDTH+j];
            assign acc_enable_wire[i][j] = acc_enable[i*WIDTH+j];
            assign sel_adder_mux_wire[i][j] = sel_adder_mux[i*WIDTH+j];
            assign sel_acc_mux_wire[i][j] = sel_acc_mux[i*WIDTH+j];
        end
    end
endgenerate

generate
    for(j=0; j<WIDTH; j=j+1)begin 
        assign b_in_wire[j] = b_in[j*ELEMENT_INPUT_WIDTH +: ELEMENT_INPUT_WIDTH];
    end
endgenerate


generate
    for(i = 0; i < HEIGHT; i = i + 1) begin : gen_row
        for(j = 0; j < WIDTH; j = j + 1) begin : gen_col
            PE #(
                .ELEMENT_INPUT_WIDTH(ELEMENT_INPUT_WIDTH),
                .ACCUMULATOR_WIDTH(ACCUMULATOR_WIDTH)
            ) pe_inst (
                .clk(clk),
                .input_enable(input_enable_wire[i][j]),
                .acc_enable(acc_enable_wire[i][j]),
                // a_in: from left edge or from previous PE in row
                .a_in(j == 0 ? a_in_wire[i]: a_wire[i][j-1]),
                // b_in: from top edge or from previous PE in column
                .b_in(i == 0 ? b_in_wire[j]: b_wire[i-1][j]),
                .sel_adder_mux(sel_adder_mux_wire[i][j]),
                .sel_acc_mux(sel_acc_mux_wire[i][j]),
                // c_in: 0 for top row, otherwise from previous PE in column
                .c_in(i == 0 ? {ACCUMULATOR_WIDTH{1'b0}} : c_wire[i-1][j]),
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
        assign c_out[(i+1)*ACCUMULATOR_WIDTH-1 : i*ACCUMULATOR_WIDTH] = c_wire[HEIGHT-1][i];
    end
endgenerate

endmodule


