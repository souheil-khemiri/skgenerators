module programmable_delay_block 
#(
    parameter   ELEMENT_INPUT_WIDTH=8,
    parameter   DEPTH=8,
    parameter   HEIGHT=8,
    parameter   SEL_DELAY_WIDTH=3 //log2(DEPTH)
)
(
    input   clk,
    input   [ELEMENT_INPUT_WIDTH*HEIGHT-1:0] D,
    input   [SEL_DELAY_WIDTH*HEIGHT-1:0] sel_delay,
    input   [HEIGHT-1:0] enable,
    output  [ELEMENT_INPUT_WIDTH*HEIGHT-1:0] Q
);


localparam integer DELAY_STAGES = (DEPTH > 1) ? (DEPTH - 1) : 1;
reg [ELEMENT_INPUT_WIDTH-1:0] delay_block [0:HEIGHT-1][0:DELAY_STAGES-1];
wire [ELEMENT_INPUT_WIDTH-1:0] D_unpacked [0:HEIGHT-1];
reg  [ELEMENT_INPUT_WIDTH-1:0] Q_unpacked [0:HEIGHT-1];
wire [SEL_DELAY_WIDTH-1:0] sel_delay_unpacked[0:HEIGHT-1];

genvar k;
generate
    for (k = 0; k < HEIGHT; k = k + 1) begin : unpack
        assign D_unpacked[k] = D[k*ELEMENT_INPUT_WIDTH +: ELEMENT_INPUT_WIDTH];
        assign Q[k*ELEMENT_INPUT_WIDTH +: ELEMENT_INPUT_WIDTH] =  Q_unpacked[k];
        assign sel_delay_unpacked[k] = sel_delay[k*SEL_DELAY_WIDTH +: SEL_DELAY_WIDTH];

    end
endgenerate
 

integer i,i_a,j;


always @(posedge clk) begin
    for (j = 0; j<HEIGHT ;j=j+1 ) begin
        if(enable[j]) begin
        delay_block[j][0] <= D_unpacked[j];
            for(i_a = 1; i_a < DELAY_STAGES; i_a = i_a + 1) begin
                delay_block[j][i_a] <= delay_block[j][i_a-1];
            end
        end
    end
end

always @(*) begin
    for (i = 0; i < HEIGHT; i = i + 1) begin
        if(sel_delay_unpacked[i] == 0 ) begin
            Q_unpacked[i] = D_unpacked[i];
        /* verilator lint_off WIDTHEXPAND */
        /* verilator lint_off CMPCONST */
        end else if(0<sel_delay_unpacked[i] && sel_delay_unpacked[i] <= DELAY_STAGES) begin
        /* verilator lint_on WIDTHEXPAND */
        /* verilator lint_off CMPCONST */
            Q_unpacked[i] = delay_block[i][sel_delay_unpacked[i] - 1];
        end else Q_unpacked[i] = {ELEMENT_INPUT_WIDTH{1'b0}};
     end
end
     
endmodule
