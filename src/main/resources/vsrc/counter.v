module counter
#(parameter xLen = 64)
(input  clk,
 input  start,
 input  reset,
 input  [xLen-1 : 0] init_val,
 input  init,
 input  return_current_count,
 output [xLen-1 : 0] current_count,
 output [xLen-1 : 0] debug_out,
 output count_valid,
 output count_valid_fsm
 );

//!!! All assignments in an always block must be declared as a reg!
reg [xLen-1 : 0] counter_reg;
reg [xLen-1 : 0] current_count_reg;
reg [xLen-1 : 0] init_val_reg;
reg return_current_count_reg;
reg init_reg;
reg start_reg;
reg count_valid_reg;
reg count_valid_fsm_reg;
reg[1:0] count_valid_timer;

//states declaration 
//Top FSM
reg[1:0] state, next_state;
parameter idle  = 2'b00;
parameter init_state  = 2'b01;
parameter count = 2'b10;
parameter current_count_state  = 2'b11;
//count_valid fsm
reg cv_state, cv_next_state;
parameter c_not_valid = 1'b0;
parameter c_valid = 1'b1;

//debug out singnal
assign debug_out = counter_reg;
assign count_valid = count_valid_reg;
assign count_valid_fsm = count_valid_fsm_reg;

//state register 
always @(posedge clk , posedge reset) begin
    if(reset) begin
        state <= idle;
        cv_state <= c_not_valid; 
    end
    else begin
        
        state <= next_state;
        cv_state <= cv_next_state;
    end
end
//Top FSM next state logic
always @(*) begin
    case(state)
        idle                : if(start_reg) next_state = count;
                              else if(init_reg) next_state = init_state;
        count               : if(return_current_count_reg) next_state = current_count_state;
        current_count_state : next_state = count;
        init_state          : next_state = idle;
        default             : next_state = idle; 
    endcase
end
//count valid FSM next state logic
always @(*) begin
    case (cv_state)
        c_not_valid             : if (next_state == current_count_state) cv_next_state = c_valid; 
        c_valid                 : if (count_valid_timer == 3 )cv_next_state = c_not_valid;
        default                 : cv_next_state = c_not_valid;
    endcase 
end
//counter logic
always @(posedge clk) begin
    if(reset) begin
        counter_reg <= 0;
        current_count_reg <= 0;
        return_current_count_reg <= 0 ;
        init_reg <= 0;
        start_reg <=0;
        count_valid_fsm_reg <=0;
        //count_valid_reg <= 0;
    end
    else if(state == idle) begin        
        if(init) begin 
            init_reg <= init;
            init_val_reg <= init_val;
        end
        else start_reg <= start;
    end
    else if (state == init_state) begin
        init_reg <= 0;
        counter_reg <= init_val_reg;
        current_count_reg <= init_val_reg;  // Update output immediately
    end
    else if (state == current_count_state) begin
        //count_valid_reg <= 0;
        current_count_reg <= counter_reg; 
        return_current_count_reg <=0;
        count_valid_fsm_reg <=1;
    end
    else if (state == count) begin
        start_reg <= 0;
        return_current_count_reg <= return_current_count;
        //if(return_current_count || return_current_count_reg) count_valid_reg <= 0;
        //else count_valid_reg <= 1;
        count_valid_fsm_reg <= 0;
        counter_reg <= counter_reg + 1;

    end
end
//count_valid logic
always @(posedge clk) begin
    if(reset) begin
        count_valid_reg <= 0;
        count_valid_timer <=0;
    end
    else if(cv_state == c_valid) begin
        count_valid_reg <= 1;
        count_valid_timer <= count_valid_timer + 1;
    end
    else if(cv_state == c_not_valid)begin
        count_valid_timer <= 0;
        count_valid_reg <= 0;
    end 
end

//output assignment
assign current_count = current_count_reg;

endmodule

