module AdderPlus
#(
    parameter WIDTH = 32,
    parameter PLUS = 1
)
(
    input clk,
    input rst,
    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    input start,
    output reg valid,
    output reg [WIDTH-1:0] sum,
    output reg ready
);

reg [WIDTH-1:0] a_reg, b_reg;
reg data_ready_reg;
reg start_reg;

always @(posedge clk) begin
    start_reg <= start;
    if(rst) begin
        data_ready_reg <=1'b0;
        valid <= 1'b0;
        ready <=1'b1;
    end else begin
        //so that valid is only high for 1 cc and the cpu does not stall
        valid <= 1'b0;

        //start state  and data acquisition
        if (start && ready) begin
            a_reg <= a;
            b_reg <= b;
            valid <= 1'b0;
            data_ready_reg <= 1'b1;
            ready <=1'b0;
        end
        //data procsessing
        else if(data_ready_reg)begin 
            sum <= a_reg + b_reg + PLUS;
            valid <= 1'b1;
            ready <= 1'b1;
            data_ready_reg <= 1'b0;
        end
    end

end
endmodule