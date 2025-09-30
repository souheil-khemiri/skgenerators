module counter_tb();
parameter xLen = 64 ;
reg clk;
reg start;
reg reset;
reg [xLen-1 : 0] init_val;
reg init;
reg return_current_count;
wire [xLen-1 : 0] current_count;
wire [xLen-1 : 0] debug_out;





counter #(.xLen(xLen)) dut(
    .clk(clk),
    .start(start),
    .reset(reset),
    .init_val(init_val),
    .init(init),
    .return_current_count(return_current_count),
    .current_count(current_count),
    .debug_out(debug_out)
);
//clock generation
//An alwyas block with no sensitivity list keeps on looping with no end
always 
    begin
        clk <= 1;
        #5;
        clk <= 0;
        #5;
    end

//Initial block stops at the last line of code
//assignments are blocking inside initial block
initial
    begin
    reset = 1;
    init = 0;
    return_current_count = 0;
    start = 0;              
    #10;                   
    reset = 0;              
    #20;
    init = 1;
    init_val = 75;
    #10;
    init = 0;
    #40;
    init = 0;
    start = 1;
    #10;
    start = 0;
    #100;
    return_current_count = 1;
    /#10;
    return_current_count=0;
    #100;
    reset = 1;
    #50;
    end
endmodule