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
    output  reg done_reset_acc,
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
reg input_enable_wire[0:HEIGHT-1][0:WIDTH-1];
reg acc_enable_wire[0:HEIGHT-1][0:WIDTH-1];
reg sel_adder_mux_wire[0:HEIGHT-1][0:WIDTH-1];
reg sel_acc_mux_wire[0:HEIGHT-1][0:WIDTH-1];
reg [SEL_DELAY_WIDTH_A-1:0] sel_delay_a_wire[0:HEIGHT-1];
reg [SEL_DELAY_WIDTH_B-1:0] sel_delay_b_wire[0:WIDTH-1];

genvar ii;
genvar jj;
generate
    for(ii=0; ii<HEIGHT; ii=ii+1)begin : gen_ctrl_row
        for (jj=0; jj<WIDTH; jj=jj+1 ) begin : gen_ctrl_col    
            assign input_enable[ii*WIDTH+jj] = input_enable_wire[ii][jj];
            assign acc_enable[ii*WIDTH+jj] = acc_enable_wire[ii][jj];
            assign sel_adder_mux[ii*WIDTH+jj] = sel_adder_mux_wire[ii][jj];
            assign sel_acc_mux[ii*WIDTH+jj] = sel_acc_mux_wire[ii][jj];
        end
    end
endgenerate
generate
    for (ii = 0;ii<HEIGHT ;ii=ii+1 ) begin :gen_sel_delay_a
        assign sel_delay_a[ii*SEL_DELAY_WIDTH_A+:SEL_DELAY_WIDTH_A] = sel_delay_a_wire[ii];
    end
endgenerate
generate
    for (ii = 0;ii<WIDTH ;ii=ii+1 ) begin :gen_sel_delay_b
        assign sel_delay_b[ii*SEL_DELAY_WIDTH_B+:SEL_DELAY_WIDTH_B] = sel_delay_b_wire[ii];
    end
endgenerate

/*internal control signals and params*/
integer i,j;
localparam RESET_CYCLES = HEIGHT;
localparam ACC_RST_COUNTER_WIDTH =32;
//reg done_reset_acc;
reg [ACC_RST_COUNTER_WIDTH-1:0] acc_rst_counter;


/*state definition*/
localparam S_idle=3'b000;
localparam S_rst=3'b001;
localparam S_rst_acc=3'b010;
localparam S_start_mac=3'b011;
localparam S_get_results=3'b100;


reg [2:0] state, next_state;

/*state registers*/
always @(posedge clk, posedge arst) begin
    if(arst) begin
        state <= S_rst;
        //...
    end else state<=next_state;
end

/*next state logic*/
always @(*) begin
    case (state)
        S_rst : if(acc_rst_counter == (RESET_CYCLES-1)) next_state = S_idle;
                    else next_state = S_rst;
        S_idle : if()
        
        default: next_state=idle 
    endcase

end

/*internal sequential logic*/
always @(posedge clk ,posedge arst) begin
    //S_rst_acc
    if(state == S_rst || state == S_rst_acc) begin
        for (i = 0 ; i<HEIGHT ;i=i+1 ) begin
            for (j = 0;j<WIDTH ;j=j+1 ) begin
                input_enable_wire[i][j]<=0;
                acc_enable_wire[i][j]<=1;
                sel_adder_mux_wire[i][j]<=0;
                sel_acc_mux_wire[i][j]<=0;
            end
        end
    end
    //Set delays
    if (state == S_rst) begin
        for (i =0 ;i<HEIGHT ; i=i+1) begin
            sel_delay_a_wire[i]<=i;
        end
        for (i =0 ;i<WIDTH ; i=i+1) begin
            sel_delay_b_wire[i]<=i;
        end
    end    
end
// acc reset counter
always @(posedge clk , posedge arst) begin
    if(arst || reset_acc ) begin
        acc_rst_counter <= ACC_RST_COUNTER_WIDTH'd0;
    end else if (state == S_rst || state == S_rst_acc) begin
        acc_rst_counter <= acc_rst_counter + ACC_RST_COUNTER_WIDTH'd1;
    end else begin
        acc_rst_counter <= ACC_RST_COUNTER_WIDTH'd0;
    end
    
end

/*output logic*/
always @(posedge clk or posedge arst) begin
  if (arst) begin
    done_reset_acc <= 1'b0;
  end else begin
    done_reset_acc <= (state == S_rst || state == S_rst_acc) &&
                      (acc_rst_counter == (RESET_CYCLES-1));
  end
end

    
endmodule