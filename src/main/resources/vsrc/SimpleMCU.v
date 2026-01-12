module SimpleMCU
#(parameter  xlen =64)
(
    input clock,
    input reset,
    input [xlen-1: 0] init_address,
    input set_init_address,
    input [xlen-1 : 0] increment,
    input set_increment,
    input [xlen-1 : 0] transfer_count,
    input set_transfer_count,
    input operation,
    input set_operation,
    input start,
    output [xlen-1 : 0] address_out,
    output reg enable,
    output reg rd_wr,
    output reg busy

);
//MCU config registers
reg [xlen-1 : 0] init_address_reg; 
reg [xlen-1 : 0] increment_reg;
reg [xlen-1 : 0] transfer_count_reg;
reg [xlen-1 : 0] address_reg;
// internal signals
reg compute_done;
reg first_address;

//output




//states
parameter idle = 2'b00;
parameter compute = 2'b01;
//states registers
reg[1:0] state, next_state;
//state transisiton
 always @(posedge clock) begin
    if(reset) begin
        state <= idle;
        enable <= 0;
        rd_wr <= 0;
        busy <= 0;
        compute_done <= 0;

    end
    else begin
       state <= next_state; 
    end
end
//FSM
always @(*) begin
    case (state)
        idle: if (start == 1) next_state = compute; else next_state = idle;
        compute: if (compute_done) next_state = idle; else next_state = compute;
        default: next_state = idle;
    endcase
end
//logic
always @(posedge clock) begin
    case (state)
        idle:begin
            if(set_init_address) begin 
                init_address_reg <= init_address;
                address_reg <= init_address;
            end
            else if(set_increment) increment_reg <= increment;
            else if(set_transfer_count) transfer_count_reg <= transfer_count;
            else if (set_operation) rd_wr <= operation;
            busy <= 0;
            compute_done <= 0;
            first_address <= 1;
        end
        compute:begin
            if(address_reg  < init_address_reg + increment_reg * (transfer_count_reg - 1)) begin
                if(first_address)begin

                    first_address <= 0;
                    busy <= 1;
                    enable <= 1;
                end
                else begin
                address_reg <= address_reg + increment_reg;
                end
            end else begin
                compute_done <= 1;
                enable <= 0;

            end 
        end
    endcase
end
assign address_out = address_reg;

endmodule