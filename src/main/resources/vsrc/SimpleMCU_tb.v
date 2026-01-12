module SimpleMCU_tb();

parameter  xlen =64;
reg clock;
reg reset;
reg [xlen-1: 0] init_address;
reg set_init_address;
reg [xlen-1 : 0] increment;
reg set_increment;
reg [xlen-1 : 0] transfer_count;
reg set_transfer_count;
reg operation;
reg set_operation;
reg start;
wire [xlen-1 : 0] address_out;
wire enable;
wire rd_wr;
wire busy;

SimpleMCU #(.xlen(xlen)) dut(
    .clock(clock),
    .reset(reset),
    .init_address(init_address),
    .set_init_address(set_init_address),
    .increment(increment),
    .set_increment(set_increment),
    .transfer_count(transfer_count),
    .set_transfer_count(set_transfer_count),
    .operation(operation),
    .set_operation(set_operation),
    .start(start),
    .address_out(address_out),
    .enable(enable),
    .rd_wr(rd_wr),
    .busy(busy)
);
localparam clk_period = 10;
//clock generation
always 
    begin
        clock <= 1;
        #5;
        clock <= 0;
        #5;
    end
initial
    begin
    reset = 1;
    # (2*clk_period);
    reset = 0;
    #clk_period;
    init_address = 10;
    set_init_address = 1;
    #clk_period;
    set_init_address = 0;
    increment = 4;
    set_increment = 1;
    #clk_period;
    set_increment = 0;
    transfer_count = 5;
    set_transfer_count = 1;
    #clk_period;
    set_transfer_count = 0;
    operation = 1; //write
    set_operation = 1;
    #clk_period;
    set_operation = 0;
    #clk_period;
    start = 1;
    #clk_period;
    start = 0;  // ✅ Deassert start
    #(100*clk_period);
    
    end

endmodule