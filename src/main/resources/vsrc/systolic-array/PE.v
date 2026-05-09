//updated
module PE 
#(
    parameter ELEMENT_INPUT_WIDTH = 8 ,
    parameter ACCUMULATOR_WIDTH  = 16 
)
(
    input  clk,
    input  input_enable,
    input  acc_enable, 
    input  signed [ELEMENT_INPUT_WIDTH-1:0]a_in,
    input  signed [ELEMENT_INPUT_WIDTH-1:0]b_in,
    input  sel_adder_mux, // 1: sel accumulator output, 0: sel zero
    input  sel_acc_mux, // 1: sel adder output, 0: sel c_in 
    input  signed [ACCUMULATOR_WIDTH-1:0]c_in,
    output reg signed [ELEMENT_INPUT_WIDTH-1:0]a_out,
    output reg signed [ELEMENT_INPUT_WIDTH-1:0]b_out,
    output signed [ACCUMULATOR_WIDTH-1:0]c_out
);

reg  signed [ACCUMULATOR_WIDTH-1:0] accumulator_output;
wire signed [ACCUMULATOR_WIDTH-1:0] product;
wire signed [ACCUMULATOR_WIDTH-1:0] sum;
wire signed [ACCUMULATOR_WIDTH-1:0] accumulator_input;

assign product = a_in * b_in;
assign sum = product + (sel_adder_mux ? accumulator_output : {ACCUMULATOR_WIDTH{1'b0}});
assign accumulator_input = sel_acc_mux ? sum : c_in;
assign c_out = accumulator_output;
always @(posedge clk ) begin 
    if(input_enable) begin
        a_out<=a_in;
        b_out<=b_in;
    end
    if(acc_enable) begin
        accumulator_output <=accumulator_input;
    end
end

endmodule
