module dpu (
	input wire         clk,
	input wire         rst_n,
	//sram controller
	input  wire        dpu_load_cmd, // from controller
	input  wire        requst_valid, // from controller
	input  wire  [7:0] nxt_cmd, 
	input  wire [31:0] sram_data_read,
	output reg  [31:0] sram_data_out,
	output wire  [4:0] sram_addr
);
//===============================================================//
// INTERNAL SIGNAL
//===============================================================//
localparam ADD  = 2'b00;
localparam SUB  = 2'b01;
localparam MUL  = 2'b10;
localparam DIV  = 2'b11;
localparam IDLE = 2'b00;
localparam RD   = 2'b01;
localparam CAL  = 2'b10;
localparam SEND = 2'b11;
reg  [7:0] cur_cmd;
reg  [1:0] cur_state;
reg  [1:0] nxt_state;
wire [1:0] mod;
reg [31:0] data_in;
reg [31:0] data_out;
reg        load;
//===============================================================//
// CMD REG
//===============================================================//
// CONFIGURATION
// [7] -> reserved, judge if we use dpu, used in sram controller
// [6:5] -> mod -- 00: +1 
//                 01: -1
//                 10: *2
//                 11: /2
// [4:0] -> reserved, sram address, used in sram controller
//===============================================================// 
always @(posedge clk, negedge rst_n) begin
	if (!rst_n) begin
		cur_cmd <= 8'b0;
	end
	else begin
		if (dpu_load_cmd) begin
			cur_cmd <= nxt_cmd;
		end
	end
end

assign sram_addr = cur_cmd[4:0];//opration on this address
assign mod       = cur_cmd[6:5];
//==============================================================//
// CONTROL PATH
//==============================================================//
always @(posedge clk, negedge rst_n) begin
	if (!rst_n) begin
		cur_state <= IDLE;
	end
	else begin
		cur_state <= nxt_state;
	end
end
always @(*) begin
	load         = 1'b0;
	case (cur_state)
		IDLE: begin
			if (dpu_load_cmd) begin
				nxt_state = RD;
			end
			else begin
				nxt_state = IDLE;
			end
		end
		RD: begin
			if (requst_valid) begin
				load = 'b1;
				nxt_state = CAL;
			end
			else begin
				nxt_state = RD;
			end
		end
		CAL: begin
			nxt_state = SEND;
		end
		SEND: begin
			if (requst_valid) begin
				nxt_state = IDLE;
			end
			else begin
				nxt_state = SEND;
			end
		end 
		default: begin
			nxt_state = IDLE;
		end

	endcase
end
//==============================================================//
// DATA PATH
//==============================================================//
always @(*) begin
	case (mod)
		ADD: begin
			data_out = data_in + 1;
		end
		SUB: begin
			data_out = data_in - 1;
		end
		MUL: begin
			data_out = data_in << 1;
		end
		DIV: begin
			data_out = data_in >> 1;
		end 
		default: begin
			data_out = data_in + 1; 
		end
	endcase
end
//==============================================================//
// DATA REGS
//==============================================================//
always @(posedge clk, negedge rst_n) begin
	if (!rst_n) begin
		data_in <= 32'b0;
	end
	else begin
		if (load) begin
		    data_in <= sram_data_read;
		end
	end
end

always @(posedge clk, negedge rst_n) begin
	if (!rst_n) begin
		sram_data_out <= 32'b0;
	end
	else begin
		sram_data_out <= data_out;
	end
end
endmodule