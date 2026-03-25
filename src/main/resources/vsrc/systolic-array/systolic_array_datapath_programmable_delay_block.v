module systolic_array_datapath_programmable_delay_block
 #(
    parameter   HEIGHT = 8,
    parameter   WIDTH = 8,
    parameter   ELEMENT_INPUT_WIDTH = 8,
    parameter   ACCUMULATOR_WIDTH = 16, //must be 2x ELEMENT_INPUT_WIDTH 
    parameter   SEL_DELAY_WIDTH_A=3, //log2(DEPTH)
    parameter   SEL_DELAY_WIDTH_B=3, //log2(DEPTH)
    parameter   DEPTH_A= HEIGHT,
    parameter   DEPTH_B= WIDTH
) (
    input  clk,
    input  [HEIGHT-1:0]input_row_enable,
    input  [WIDTH-1:0]input_col_enable,
    input  [HEIGHT-1:0]acc_row_enable,
    input  [WIDTH-1:0]acc_col_enable, 
    input  [ELEMENT_INPUT_WIDTH*HEIGHT-1:0]a_in,
    input  [ELEMENT_INPUT_WIDTH*WIDTH-1:0]b_in,
    input  [HEIGHT-1:0]sel_row_adder_mux, // 1: sel accumulator output, 0: sel zero
    input  [WIDTH-1:0]sel_col_adder_mux, // 1: sel accumulator output, 0: sel zero
    input  [HEIGHT-1:0]sel_row_acc_mux, // 1: sel adder output, 0: sel c_in
    input  [WIDTH-1:0]sel_col_acc_mux, // 1: sel adder output, 0: sel c_in
    input  [SEL_DELAY_WIDTH_A*HEIGHT-1:0] sel_delay_a,
    input  [HEIGHT-1:0] delay_enable_a,
    input  [SEL_DELAY_WIDTH_B*WIDTH-1:0] sel_delay_b,
    input  [WIDTH-1:0] delay_enable_b,
    output [ACCUMULATOR_WIDTH*WIDTH-1:0] c_out  

);


wire [ELEMENT_INPUT_WIDTH*HEIGHT-1:0] a_wire;
wire [ELEMENT_INPUT_WIDTH*WIDTH-1:0] b_wire;


systolic_array_datapath # (
    .HEIGHT(HEIGHT),
    .WIDTH(WIDTH),
    .ELEMENT_INPUT_WIDTH(ELEMENT_INPUT_WIDTH),
    .ACCUMULATOR_WIDTH(ACCUMULATOR_WIDTH)
  )
  systolic_array_datapath_inst (
    .clk(clk),
    .input_row_enable(input_row_enable),
    .input_col_enable(input_col_enable),
    .acc_row_enable(acc_row_enable),
    .acc_col_enable(acc_col_enable),
    .a_in(a_wire),
    .b_in(b_wire),
    .sel_row_adder_mux(sel_row_adder_mux),
    .sel_col_adder_mux(sel_col_adder_mux),
    .sel_row_acc_mux(sel_row_acc_mux),
    .sel_col_acc_mux(sel_col_acc_mux),
    .c_out(c_out)
  );    

  programmable_delay_block # (
    .ELEMENT_INPUT_WIDTH(ELEMENT_INPUT_WIDTH),
    .DEPTH(DEPTH_A),
    .HEIGHT(HEIGHT),
    .SEL_DELAY_WIDTH(SEL_DELAY_WIDTH_A)
  )
  programmable_delay_block_inst_a (
    .clk(clk),
    .D(a_in),
    .sel_delay(sel_delay_a),
    .enable(delay_enable_a),
    .Q(a_wire)
  );

  programmable_delay_block # (
    .ELEMENT_INPUT_WIDTH(ELEMENT_INPUT_WIDTH),
    .DEPTH(DEPTH_B),
    .HEIGHT(WIDTH),
    .SEL_DELAY_WIDTH(SEL_DELAY_WIDTH_B)
  )
  programmable_delay_block_inst_b (
    .clk(clk),
    .D(b_in),
    .sel_delay(sel_delay_b),
    .enable(delay_enable_b),
    .Q(b_wire)
  );

endmodule
