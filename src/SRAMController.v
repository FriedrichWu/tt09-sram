module SRAMController (
	input wire clk,
	input wire rst_n,
	// tx 
	input wire tx_ready,
	output reg tx_enable,
	output reg tx_valid, 
	output reg [7:0] tx_data_in,
	// rx
	input wire [7:0] rx_data_out,
	input wire rx_valid,
	output reg rx_enable,
	output reg rx_ready,
	// sram
	output reg csb_n,
	output reg we_n,
	input wire [4:0] addr,
	input wire [31:0] sram_data_out,
	output reg [31:0] sram_data_in
);
//=====================================//
//==========INTERNAL_SIGNAL============//
//=====================================//
localparam IDLE = 'b0000;
localparam RD_0 = 'b0001;
localparam RD_1 = 'b0010;
localparam RD_2 = 'b0011;
localparam RD_3 = 'b0100;
localparam WD_0 = 'b0101;
localparam WD_1 = 'b0110;
localparam WD_2 = 'b0111;
localparam WD_3 = 'b1000;
localparam WRITE = 'b1001;
reg [2:0] cur_state;
reg [2:0] nxt_state;
reg [7:0] addr_tmp;
reg [31:0] data_tmp;
wire addr_tmp_en;
wire data_tmp_en;
//============ADDR_TMP_REG==============//
always @(posedge clk, negedge rst_n) begin
	if (!rst_n) begin
		addr_tmp <= 'b0;
	end
	else begin
		if (addr_tmp_en) begin
			addr_tmp <= rx_data_out;
		end
	end
end
//=============DATA_TMP_REG=============//
always @(posedge clk, negedge rst_n) begin
	if (!rst_n) begin
		data_tmp <= 'b0;
	end
	else begin
		if (data_tmp_en) begin
			data_tmp <= {data_tmp[23:0], rx_data_out};
		end
	end
end
//======================================//
//============STATE_MACHINE=============//
//======================================//
always @(posedge clk, negedge rst_n) begin
	if (!rst_n) begin
		cur_state <= IDLE;
	end
	else begin
		cur_state <= nxt_state;
	end
end

always @(*) begin
	//defualt value
	addr_tmp_en = 'b0;
	we_n        = 'b0;
	csb_n       = 'b1;
	tx_enable   = 'b0;
	tx_valid    = 'b0; 
	rx_ready = 'b0;
	data_tmp_en = 'b0;
	case (cur_state)
		IDLE: begin
			if (rx_valid) begin
				if (rx_data_out[5] == 'b1) begin // read 
                    we_n = 'b1;
					csb_n = 'b0;
					addr = rx_data_out[4:0];
					rx_ready = 'b1;
					nxt_state = RD_0;
				end 
				else begin // write
					addr_tmp_en = 'b1;// store the address
					rx_ready = 'b1;
					nxt_state = WD_0;
				end
			end
			else begin
				nxt_state = IDLE;
			end
		end 
		RD_0: begin
			if (tx_ready) begin
				tx_enable = 'b1;
				tx_data_in = sram_data_out[7:0];	
				tx_valid = 'b1;
				nxt_state = RD_1;
			end
			else begin
				nxt_state = RD_0;
			end
		end
		RD_1: begin
			if (tx_ready) begin
				tx_enable = 'b1;
				tx_data_in = sram_data_out[15:8];
				tx_valid = 'b1;
				nxt_state = RD_2;
			end
			else begin
				nxt_state = RD_1;
			end
		end
		RD_2: begin
			if (tx_ready) begin
				tx_enable = 'b1;
				tx_data_in = sram_data_out[23:16];
				tx_valid = 'b1;
				nxt_state = RD_3;
			end
			else begin
				nxt_state = RD_2;
			end
		end
		RD_3: begin
			if (tx_ready) begin
				tx_enable = 'b1;
				tx_data_in = sram_data_out[31:24];
				tx_valid = 'b1;
				nxt_state = IDLE;
			end
			else begin
				nxt_state = RD_3;
			end
		end
		WD_0: begin
			if (rx_valid) begin
				data_tmp_en = 'b1;
				rx_ready = 'b1;
				nxt_state = WD_1;
			end
			else begin
				nxt_state = WD_0;
			end
		end
		WD_1: begin
			if (rx_valid) begin
				data_tmp_en = 'b1;
				rx_ready = 'b1;
				nxt_state = WD_2;
			end
			else begin
				nxt_state = WD_1;
			end
		end
		WD_2: begin
			if (rx_valid) begin
				data_tmp_en = 'b1;
				rx_ready = 'b1;
				nxt_state = WD_3;
			end
			else begin
				nxt_state = WD_2;
			end
		end
		WD_3: begin
			if (rx_valid) begin
				data_tmp_en = 'b1;
				rx_ready = 'b1;
				nxt_state = WRITE;
			end
			else begin
				nxt_state = WD_3;
			end
		end
		WRITE: begin
            we_n = 'b1;
			csb_n = 'b0;
			addr = rx_data_out[4:0];
			sram_data_in = data_tmp;	
			nxt_state = IDLE;
		end
		default: begin
			nxt_state = IDLE;
		end 
	endcase
end
endmodule
