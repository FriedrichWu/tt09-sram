module SRAMController (
	input wire        clk,
	input wire        rst_n,
	output reg        uart_ready,
	// tx 
	input wire        tx_ready,
	output reg        tx_enable,
	output reg        tx_valid, 
	output reg [ 7:0] tx_data_in,
	// rx
	input wire [ 7:0] rx_data_out,
	input wire        rx_valid,
	output reg        rx_enable,
	output reg        rx_ready,
	// sram
	output reg        csb_n,
	output reg        we_n,
	output reg [ 4:0] addr,
	input wire [31:0] sram_data_out,
	output reg [31:0] sram_data_in,
	// dpu
	output  reg        dpu_load_cmd, // from controller
	output  reg        requst_valid, // from controller
	output  reg  [7:0] nxt_cmd, 
	output  reg [31:0] sram_data_to_dpu,
	input  wire [31:0] sram_data_from_dpu,
	input  wire  [4:0] sram_addr_from_dpu
);
//=====================================//
//==========INTERNAL_SIGNAL============//
//=====================================//
localparam IDLE       = 4'b0000;
localparam READ_STORE = 4'b0001;
localparam RD_0       = 4'b0010;
localparam RD_1       = 4'b0011;
localparam RD_2       = 4'b0100;
localparam RD_3       = 4'b0101;
localparam WD_0       = 4'b0110;
localparam WD_1       = 4'b0111;
localparam WD_2       = 4'b1000;
localparam WD_3       = 4'b1001;
localparam WRITE      = 4'b1010;
localparam DPU        = 4'b1011;
localparam DPU_TMP    = 4'b1111;
localparam DPU_RD     = 4'b1100;
localparam DPU_WD     = 4'b1101;
localparam DPU_FIN    = 4'b1110;
reg [ 3:0] cur_state;
reg [ 3:0] nxt_state;
reg [ 7:0] addr_tmp;
reg [31:0] data_tmp;
reg [31:0] sram_tmp;
reg        addr_tmp_en;
reg        data_tmp_en;
reg        sram_tmp_en;
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
			data_tmp <= {rx_data_out, data_tmp[31:8]};
		end
	end
end
//==============SRAM_TMP_REG============//
// store the dout0 port information at sram, otherwire the data will be lost 
always @(posedge clk, negedge rst_n) begin
	if (!rst_n) begin
		sram_tmp <= 'b0;
	end
	else begin
		if (sram_tmp_en) begin
			sram_tmp <= sram_data_out;
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
	addr_tmp_en      = 'b0;
	we_n             = 'b0;
	csb_n            = 'b1;
	tx_enable        = 'b0;
	tx_valid         = 'b0; 
	rx_ready         = 'b0;
	data_tmp_en      = 'b0;
	rx_enable        = 'b1;
	addr             = 'b0;
	sram_data_in     = 'b0;
	tx_data_in       = 'b0;
	sram_tmp_en      = 'b0;
	dpu_load_cmd     = 'b0;
	requst_valid     = 'b0;
	nxt_cmd          = 'b0;
	sram_data_to_dpu = 'b0;
	uart_ready       = 'b0;
	case (cur_state)
		IDLE: begin
			uart_ready = 'b1;
			if (rx_valid) begin
				if (rx_data_out[7] == 'b1) begin // dpu
					dpu_load_cmd = 'b1;
					nxt_cmd = rx_data_out;
					rx_ready ='b1;
					nxt_state = DPU;
				end
				else begin
				    if (rx_data_out[5] == 'b1) begin // read 
                        we_n      = 'b1;
					    csb_n     = 'b0;
					    addr      = rx_data_out[4:0];
					    rx_ready  = 'b1;
					    nxt_state = READ_STORE;
				    end 
				    else begin // write
					    addr_tmp_en = 'b1;// store the address
					    rx_ready    = 'b1;
					    nxt_state   = WD_0;
				    end
				end
			end
			else begin
				nxt_state = IDLE;
			end
		end 
		READ_STORE: begin
			sram_tmp_en = 'b1;
			tx_enable   = 'b1;
			nxt_state   = RD_0;
		end
		RD_0: begin
			if (tx_ready) begin
				tx_enable  = 'b1;
				tx_data_in = sram_tmp[7:0];	
				tx_valid   = 'b1;
				nxt_state  = RD_1;
			end
			else begin
				tx_enable = 'b1;
				nxt_state = RD_0;
			end
		end
		RD_1: begin
			if (tx_ready) begin
				tx_enable  = 'b1;
				tx_data_in = sram_tmp[15:8];
				tx_valid   = 'b1;
				nxt_state  = RD_2;
			end
			else begin
				tx_enable = 'b1;
				nxt_state = RD_1;
			end
		end
		RD_2: begin
			if (tx_ready) begin
				tx_enable  = 'b1;
				tx_data_in = sram_tmp[23:16];
				tx_valid   = 'b1;
				nxt_state  = RD_3;
			end
			else begin
				tx_enable = 'b1;
				nxt_state = RD_2;
			end
		end
		RD_3: begin
			if (tx_ready) begin
				tx_enable  = 'b1;
				tx_data_in = sram_tmp[31:24];
				tx_valid   = 'b1;
				nxt_state  = IDLE;
			end
			else begin
				tx_enable = 'b1;
				nxt_state = RD_3;
			end
		end
		WD_0: begin
			if (rx_valid) begin
				data_tmp_en = 'b1;
				rx_ready    = 'b1;
				nxt_state   = WD_1;
			end
			else begin
				nxt_state = WD_0;
			end
		end
		WD_1: begin
			if (rx_valid) begin
				data_tmp_en = 'b1;
				rx_ready    = 'b1;
				nxt_state   = WD_2;
			end
			else begin
				nxt_state = WD_1;
			end
		end
		WD_2: begin
			if (rx_valid) begin
				data_tmp_en = 'b1;
				rx_ready    = 'b1;
				nxt_state   = WD_3;
			end
			else begin
				nxt_state = WD_2;
			end
		end
		WD_3: begin
			if (rx_valid) begin
				data_tmp_en = 'b1;
				rx_ready    = 'b1;
				nxt_state   = WRITE;
			end
			else begin
				nxt_state = WD_3;
			end
		end
		WRITE: begin
            we_n         = 'b0;
			csb_n        = 'b0;
			addr         = addr_tmp[4:0];
			sram_data_in = data_tmp;	
			nxt_state    = IDLE;
		end
		DPU: begin
			we_n      = 'b1;
			csb_n     = 'b0;
			addr      = sram_addr_from_dpu;
			nxt_state = DPU_TMP;
		end
		DPU_TMP: begin // the data read from sram will be saved 
			sram_tmp_en = 'b1;
			nxt_state   = DPU_RD;
		end
		DPU_RD: begin // transfer the data read to dpu
			sram_data_to_dpu = sram_tmp;
			requst_valid     = 'b1;
			nxt_state        = DPU_WD;
		end
		DPU_WD: begin // during this state, the dpu is calculating the data, and put it in the dpu output
			nxt_state    = DPU_FIN;
		end
		DPU_FIN: begin
			we_n         = 'b0;
			csb_n        ='b0;
			addr         = sram_addr_from_dpu;
			sram_data_in = sram_data_from_dpu;
			requst_valid = 'b1;
			nxt_state    = IDLE;
		end
		default: begin
			nxt_state = IDLE;
		end 
	endcase
end
endmodule
