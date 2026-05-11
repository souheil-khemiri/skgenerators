module control_path_SADPPDB 
#(
    parameter   HEIGHT = 8,
    parameter   WIDTH = 8,
    //parameter   ELEMENT_INPUT_WIDTH = 8,
    //parameter   ACCUMULATOR_WIDTH = 16, //must be 2x ELEMENT_INPUT_WIDTH 
    parameter   SEL_DELAY_WIDTH_A=3, //log2(DEPTH)
    parameter   SEL_DELAY_WIDTH_B=3, //log2(DEPTH)
    parameter   DEPTH_A= HEIGHT,
    parameter   DEPTH_B= WIDTH

)(
    input   clk,
    input   arst,
    input   m_inner_dimension,//A(NXM)xB(MxP)
    input   mac,
    input   reset_acc,
    input   shift_results,
    output  done_mac,
    output  done_shift_result,
    output  busy,
    output  [HEIGHT*WIDTH-1:0]input_enable,
    output  [HEIGHT*WIDTH-1:0]acc_enable,
    output  [HEIGHT*WIDTH-1:0]sel_adder_mux, // 1: sel accumulator output, 0: sel zero
    output  [HEIGHT*WIDTH-1:0]sel_acc_mux, // 1: sel adder output, 0: sel c_in 
    output  [SEL_DELAY_WIDTH_A*HEIGHT-1:0] sel_delay_a,
    output  [HEIGHT-1:0] delay_enable_a,
    output  [SEL_DELAY_WIDTH_B*WIDTH-1:0] sel_delay_b,
    output  [WIDTH-1:0] delay_enable_b

);
/*
A Finite state machine is composed of 3 logic block:
    1-Sequential block: state registers
    2-Combinational block:  compute Next state logic
    3-Output based on :
        --Only current state : Moore machine
        --Current state and input : Mealy machine
States definition:        
The localparam statement is used to define constants within a
module. Naming the states with parameters is not required,
but it makes changing state encodings much easier and
makes the code more readable.
*/




/*unpacking/unflattening signals*/
wire input_enable_wire[0:HEIGHT-1][0:WIDTH-1];
wire acc_enable_wire[0:HEIGHT-1][0:WIDTH-1];
wire sel_adder_mux_wire[0:HEIGHT-1][0:WIDTH-1];
wire sel_acc_mux_wire[0:HEIGHT-1][0:WIDTH-1];
wire [SEL_DELAY_WIDTH_A-1:0] sel_delay_a_wire[0:HEIGHT-1];
wire [SEL_DELAY_WIDTH_B-1:0] sel_delay_b_wire[0:WIDTH-1];

genvar i;
genvar j;
generate
    for(i=0; i<HEIGHT; i=i+1)begin : gen_ctrl_row
        for (j=0; j<WIDTH; j=j+1 ) begin : gen_ctrl_col    
            assign input_enable[i*WIDTH+j] = input_enable_wire[i][j];
            assign acc_enable[i*WIDTH+j] = acc_enable_wire[i][j];
            assign sel_adder_mux[i*WIDTH+j] = sel_adder_mux_wire[i][j];
            assign sel_acc_mux[i*WIDTH+j] = sel_acc_mux_wire[i][j];
        end
    end
endgenerate
generate
    for (i = 0;i<HEIGHT ;i=i+1 ) begin :gen_sel_delay_a
        assign sel_delay_a[i*SEL_DELAY_WIDTH_A+:SEL_DELAY_WIDTH_A] = sel_delay_a_wire[i]
    end
endgenerate
generate
    for (i = 0;i<WIDTH ;i=i+1 ) begin :gen_sel_delay_b
        sel_delay_b[i*SEL_DELAY_WIDTH_B+:SEL_DELAY_WIDTH_B] = sel_delay_a_wire[i]
    end
endgenerate

/*internal control signals*/
reg done_reset_acc
reg rese;


/*state definition*/
localparam S_idle=3'b000;
localparam S_rst_acc=3'b001;
localparam S_rst_set_delays=3'b010;
localparam S_start_mac=3'b011;
localparam S_get_results=3'b100;
localparam S_rst = 3'b101;
localparam

reg [2:0] state, next_state;
reg [2:0] rst_state, rst_next_state;

/*state registers*/
always @(posedge clk, posedge arst) begin
    if(arst) state <= S_rst;
    else state<=next_state;
end

/*next state logic*/
always @(*) begin
    case (state)
        P_rst : if(rst_state == ) next_state = idle;
                    else next_state = S_set_delays;
        S_ : if()
        
        default: next_state=idle 
    endcase

end

/*internal sequential logic*/
always @(posedge clk ,posedge arst) begin
    if(arst) begin
        
    end    
end
always @(*) begin
    done_reset_acc = (state==S_rst_acc) && 
end

/*output logic*/


    
endmodule