// Simple, self-contained example showing a config regfile, control FSM,
// and datapath. Config is written by a programmer, then latched on start.

module example_regfile #(
	parameter M_WIDTH = 8,
	parameter DELAY_WIDTH = 3
) (
	input  clk,
	input  arst,
	input  cfg_we,
	input  [1:0] cfg_addr,
	input  [31:0] cfg_wdata,
	output reg [M_WIDTH-1:0] cfg_M,
	output reg [DELAY_WIDTH-1:0] cfg_sel_delay_a,
	output reg [DELAY_WIDTH-1:0] cfg_sel_delay_b
);
	always @(posedge clk or posedge arst) begin
		if (arst) begin
			cfg_M <= {M_WIDTH{1'b0}};
			cfg_sel_delay_a <= {DELAY_WIDTH{1'b0}};
			cfg_sel_delay_b <= {DELAY_WIDTH{1'b0}};
		end else if (cfg_we) begin
			case (cfg_addr)
				2'b00: cfg_M <= cfg_wdata[M_WIDTH-1:0];
				2'b01: cfg_sel_delay_a <= cfg_wdata[DELAY_WIDTH-1:0];
				2'b10: cfg_sel_delay_b <= cfg_wdata[DELAY_WIDTH-1:0];
				default: begin end
			endcase
		end
	end
endmodule

module example_control_fsm #(
	parameter M_WIDTH = 8
) (
	input  clk,
	input  arst,
	input  start,
	input  [M_WIDTH-1:0] M_run,
	output reg busy,
	output reg done,
	output reg do_load,
	output reg do_run
);
	localparam S_IDLE = 2'b00;
	localparam S_LOAD = 2'b01;
	localparam S_RUN  = 2'b10;
	localparam S_DONE = 2'b11;

	reg [1:0] state, next_state;
	reg [M_WIDTH-1:0] run_count;

	always @(posedge clk or posedge arst) begin
		if (arst) begin
			state <= S_IDLE;
			run_count <= {M_WIDTH{1'b0}};
		end else begin
			state <= next_state;
			if (state == S_LOAD) begin
				run_count <= M_run;
			end else if (state == S_RUN) begin
				if (run_count != 0) begin
					run_count <= run_count - 1'b1;
				end
			end
		end
	end

	always @(*) begin
		busy = (state == S_LOAD) || (state == S_RUN);
		done = (state == S_DONE);
		do_load = (state == S_LOAD);
		do_run = (state == S_RUN);
		next_state = state;

		case (state)
			S_IDLE: if (start) next_state = S_LOAD;
			S_LOAD: if (M_run == 0) next_state = S_DONE; else next_state = S_RUN;
			S_RUN:  if (run_count == 0) next_state = S_DONE;
			S_DONE: next_state = S_IDLE;
			default: next_state = S_IDLE;
		endcase
	end
endmodule

module example_datapath #(
	parameter M_WIDTH = 8,
	parameter DELAY_WIDTH = 3,
	parameter ACC_WIDTH = 16
) (
	input  clk,
	input  arst,
	input  do_load,
	input  do_run,
	input  [M_WIDTH-1:0] M_run,
	input  [DELAY_WIDTH-1:0] sel_delay_a_run,
	input  [DELAY_WIDTH-1:0] sel_delay_b_run,
	output reg [ACC_WIDTH-1:0] result
);
	reg [ACC_WIDTH-1:0] acc;

	wire [ACC_WIDTH-1:0] M_ext = {{(ACC_WIDTH-M_WIDTH){1'b0}}, M_run};
	wire [ACC_WIDTH-1:0] a_ext = {{(ACC_WIDTH-DELAY_WIDTH){1'b0}}, sel_delay_a_run};
	wire [ACC_WIDTH-1:0] b_ext = {{(ACC_WIDTH-DELAY_WIDTH){1'b0}}, sel_delay_b_run};

	always @(posedge clk or posedge arst) begin
		if (arst) begin
			acc <= {ACC_WIDTH{1'b0}};
		end else if (do_load) begin
			acc <= {ACC_WIDTH{1'b0}};
		end else if (do_run) begin
			acc <= acc + M_ext + a_ext + b_ext;
		end
	end

	always @(*) begin
		result = acc;
	end
endmodule

module example_top #(
	parameter M_WIDTH = 8,
	parameter DELAY_WIDTH = 3,
	parameter ACC_WIDTH = 16
) (
	input  clk,
	input  arst,
	input  cfg_we,
	input  [1:0] cfg_addr,
	input  [31:0] cfg_wdata,
	input  start,
	output busy,
	output done,
	output [ACC_WIDTH-1:0] result
);
	wire [M_WIDTH-1:0] cfg_M;
	wire [DELAY_WIDTH-1:0] cfg_sel_delay_a;
	wire [DELAY_WIDTH-1:0] cfg_sel_delay_b;

	reg [M_WIDTH-1:0] M_run;
	reg [DELAY_WIDTH-1:0] sel_delay_a_run;
	reg [DELAY_WIDTH-1:0] sel_delay_b_run;

	wire do_load;
	wire do_run;

	example_regfile #(
		.M_WIDTH(M_WIDTH),
		.DELAY_WIDTH(DELAY_WIDTH)
	) regfile_inst (
		.clk(clk),
		.arst(arst),
		.cfg_we(cfg_we),
		.cfg_addr(cfg_addr),
		.cfg_wdata(cfg_wdata),
		.cfg_M(cfg_M),
		.cfg_sel_delay_a(cfg_sel_delay_a),
		.cfg_sel_delay_b(cfg_sel_delay_b)
	);

	// Snapshot config on start so it stays stable during the run.
	always @(posedge clk or posedge arst) begin
		if (arst) begin
			M_run <= {M_WIDTH{1'b0}};
			sel_delay_a_run <= {DELAY_WIDTH{1'b0}};
			sel_delay_b_run <= {DELAY_WIDTH{1'b0}};
		end else if (start && !busy) begin
			M_run <= cfg_M;
			sel_delay_a_run <= cfg_sel_delay_a;
			sel_delay_b_run <= cfg_sel_delay_b;
		end
	end

	example_control_fsm #(
		.M_WIDTH(M_WIDTH)
	) control_inst (
		.clk(clk),
		.arst(arst),
		.start(start),
		.M_run(M_run),
		.busy(busy),
		.done(done),
		.do_load(do_load),
		.do_run(do_run)
	);

	example_datapath #(
		.M_WIDTH(M_WIDTH),
		.DELAY_WIDTH(DELAY_WIDTH),
		.ACC_WIDTH(ACC_WIDTH)
	) datapath_inst (
		.clk(clk),
		.arst(arst),
		.do_load(do_load),
		.do_run(do_run),
		.M_run(M_run),
		.sel_delay_a_run(sel_delay_a_run),
		.sel_delay_b_run(sel_delay_b_run),
		.result(result)
	);
endmodule
