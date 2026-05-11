// Register-bank templates for config storage.
// - regbank_single: write only when !busy (simple rule).
// - regbank_double_buffer: write inactive bank, swap on boundary.
// - regbank_shadow_commit: write shadow, copy to active on commit.
// NOTE: This template exposes cfg0..cfg9. If you want more or fewer,
// update the port list and assignments to match.

module regfile #(
	parameter DATA_WIDTH = 8,
	parameter ADDR_WIDTH = 4
) (
	input  clk,
	input  arst,
	input  busy,
	input  cfg_we,
	input  [ADDR_WIDTH-1:0] cfg_addr,
	input  [DATA_WIDTH-1:0] cfg_wdata,
	output [DATA_WIDTH-1:0] cfg0,
	output [DATA_WIDTH-1:0] cfg1,
	output [DATA_WIDTH-1:0] cfg2,
	output [DATA_WIDTH-1:0] cfg3,
	output [DATA_WIDTH-1:0] cfg4,
	output [DATA_WIDTH-1:0] cfg5,
	output [DATA_WIDTH-1:0] cfg6,
	output [DATA_WIDTH-1:0] cfg7,
	output [DATA_WIDTH-1:0] cfg8,
	output [DATA_WIDTH-1:0] cfg9
);
	localparam DEPTH = 10;
	reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
	integer i;

	always @(posedge clk or posedge arst) begin
		if (arst) begin
			for (i = 0; i < DEPTH; i = i + 1) begin
				mem[i] <= {DATA_WIDTH{1'b0}};
			end
		end else if (cfg_we && !busy) begin
			mem[cfg_addr] <= cfg_wdata;
		end
	end

	assign cfg0 = mem[0];
	assign cfg1 = mem[1];
	assign cfg2 = mem[2];
	assign cfg3 = mem[3];
	assign cfg4 = mem[4];
	assign cfg5 = mem[5];
	assign cfg6 = mem[6];
	assign cfg7 = mem[7];
	assign cfg8 = mem[8];
	assign cfg9 = mem[9];
endmodule

module regbank_double_buffer #(
	parameter DATA_WIDTH = 8,
	parameter ADDR_WIDTH = 4
) (
	input  clk,
	input  arst,
	input  cfg_we,
	input  [ADDR_WIDTH-1:0] cfg_addr,
	input  [DATA_WIDTH-1:0] cfg_wdata,
	input  swap,
	output [DATA_WIDTH-1:0] cfg0,
	output [DATA_WIDTH-1:0] cfg1,
	output [DATA_WIDTH-1:0] cfg2,
	output [DATA_WIDTH-1:0] cfg3,
	output [DATA_WIDTH-1:0] cfg4,
	output [DATA_WIDTH-1:0] cfg5,
	output [DATA_WIDTH-1:0] cfg6,
	output [DATA_WIDTH-1:0] cfg7,
	output [DATA_WIDTH-1:0] cfg8,
	output [DATA_WIDTH-1:0] cfg9,
	output reg active_bank
);
	localparam DEPTH = 10;
	reg [DATA_WIDTH-1:0] mem0 [0:DEPTH-1];
	reg [DATA_WIDTH-1:0] mem1 [0:DEPTH-1];
	integer j;

	always @(posedge clk or posedge arst) begin
		if (arst) begin
			active_bank <= 1'b0;
			for (j = 0; j < DEPTH; j = j + 1) begin
				mem0[j] <= {DATA_WIDTH{1'b0}};
				mem1[j] <= {DATA_WIDTH{1'b0}};
			end
		end else begin
			if (swap) begin
				active_bank <= ~active_bank;
			end
			if (cfg_we) begin
				if (active_bank) begin
					mem0[cfg_addr] <= cfg_wdata;
				end else begin
					mem1[cfg_addr] <= cfg_wdata;
				end
			end
		end
	end

	assign cfg0 = active_bank ? mem1[0] : mem0[0];
	assign cfg1 = active_bank ? mem1[1] : mem0[1];
	assign cfg2 = active_bank ? mem1[2] : mem0[2];
	assign cfg3 = active_bank ? mem1[3] : mem0[3];
	assign cfg4 = active_bank ? mem1[4] : mem0[4];
	assign cfg5 = active_bank ? mem1[5] : mem0[5];
	assign cfg6 = active_bank ? mem1[6] : mem0[6];
	assign cfg7 = active_bank ? mem1[7] : mem0[7];
	assign cfg8 = active_bank ? mem1[8] : mem0[8];
	assign cfg9 = active_bank ? mem1[9] : mem0[9];
endmodule

module regbank_shadow_commit #(
	parameter DATA_WIDTH = 8,
	parameter ADDR_WIDTH = 4
) (
	input  clk,
	input  arst,
	input  cfg_we,
	input  [ADDR_WIDTH-1:0] cfg_addr,
	input  [DATA_WIDTH-1:0] cfg_wdata,
	input  commit,
	output [DATA_WIDTH-1:0] cfg0,
	output [DATA_WIDTH-1:0] cfg1,
	output [DATA_WIDTH-1:0] cfg2,
	output [DATA_WIDTH-1:0] cfg3,
	output [DATA_WIDTH-1:0] cfg4,
	output [DATA_WIDTH-1:0] cfg5,
	output [DATA_WIDTH-1:0] cfg6,
	output [DATA_WIDTH-1:0] cfg7,
	output [DATA_WIDTH-1:0] cfg8,
	output [DATA_WIDTH-1:0] cfg9
);
	localparam DEPTH = 10;
	reg [DATA_WIDTH-1:0] shadow [0:DEPTH-1];
	reg [DATA_WIDTH-1:0] active [0:DEPTH-1];
	integer k;

	always @(posedge clk or posedge arst) begin
		if (arst) begin
			for (k = 0; k < DEPTH; k = k + 1) begin
				shadow[k] <= {DATA_WIDTH{1'b0}};
				active[k] <= {DATA_WIDTH{1'b0}};
			end
		end else begin
			if (commit) begin
				for (k = 0; k < DEPTH; k = k + 1) begin
					active[k] <= shadow[k];
				end
			end
			if (cfg_we) begin
				shadow[cfg_addr] <= cfg_wdata;
			end
		end
	end

	assign cfg0 = active[0];
	assign cfg1 = active[1];
	assign cfg2 = active[2];
	assign cfg3 = active[3];
	assign cfg4 = active[4];
	assign cfg5 = active[5];
	assign cfg6 = active[6];
	assign cfg7 = active[7];
	assign cfg8 = active[8];
	assign cfg9 = active[9];
endmodule

module regbank_shadow_commit_sa #(
	parameter DATA_WIDTH = 8,
	parameter ADDR_WIDTH = 4
) (
	input  clk,
	input  arst,
	input  cfg_we,
	input  [ADDR_WIDTH-1:0] cfg_addr,
	input  [DATA_WIDTH-1:0] cfg_wdata,
	input  commit,
	output [DATA_WIDTH-1:0] cm_inner_dimension,
	output [DATA_WIDTH-1:0] cfg1,
	output [DATA_WIDTH-1:0] cfg2,
	output [DATA_WIDTH-1:0] cfg3,
	output [DATA_WIDTH-1:0] cfg4,
	output [DATA_WIDTH-1:0] cfg5,
	output [DATA_WIDTH-1:0] cfg6,
	output [DATA_WIDTH-1:0] cfg7,
	output [DATA_WIDTH-1:0] cfg8,
	output [DATA_WIDTH-1:0] cfg9
);
	localparam DEPTH = 10;
	reg [DATA_WIDTH-1:0] shadow [0:DEPTH-1];
	reg [DATA_WIDTH-1:0] active [0:DEPTH-1];
	integer k;

	always @(posedge clk or posedge arst) begin
		if (arst) begin
			for (k = 0; k < DEPTH; k = k + 1) begin
				shadow[k] <= {DATA_WIDTH{1'b0}};
				active[k] <= {DATA_WIDTH{1'b0}};
			end
		end else begin
			if (commit) begin
				for (k = 0; k < DEPTH; k = k + 1) begin
					active[k] <= shadow[k];
				end
			end
			if (cfg_we) begin
				shadow[cfg_addr] <= cfg_wdata;
			end
		end
	end

	assign m_inner_dimension = active[0];
	assign cfg1 = active[1];
	assign cfg2 = active[2];
	assign cfg3 = active[3];
	assign cfg4 = active[4];
	assign cfg5 = active[5];
	assign cfg6 = active[6];
	assign cfg7 = active[7];
	assign cfg8 = active[8];
	assign cfg9 = active[9];
endmodule