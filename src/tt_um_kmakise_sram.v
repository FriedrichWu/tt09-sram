/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_kmakise_sram (
`ifdef USE_POWER_PINS
    inout             VDPWR,
    inout             VGND,
`endif
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
//the bi-direction IO
assign uio_oe     = 8'b00010000; 
assign uio_out[7] = 1'b0;
assign uio_out[6] = 1'b0;
assign uio_out[5] = 1'b0;
assign uio_out[3] = 1'b0;
assign uio_out[2] = 1'b0;
assign uio_out[1] = 1'b0;
assign uio_out[0] = 1'b0;
//the noraml output IO
assign uo_out[1] = 1'b0;
assign uo_out[2] = 1'b0;
assign uo_out[3] = 1'b0;
assign uo_out[4] = 1'b0;
assign uo_out[5] = 1'b0;

wire        reset;
wire        rx_enable;
wire        rx_ready;
wire        rx_valid;
wire [ 7:0] rx_data_out;
wire        tx_enable;
wire        tx_valid;
wire [ 7:0] tx_data_in;
wire        tx_ready;
wire        csb_n;
wire        we_n;
wire [ 4:0] addr;
wire [31:0] sram_data_in;
wire [31:0] sram_data_out;
//wire [32:0] sram_data_out_full;
//wire [32:0] sram_data_in_full;
wire        rx_in;
wire        tx_out;
wire        dpu_load_cmd;
wire        requst_valid;
wire [ 7:0] nxt_cmd;
wire [31:0] sram_data_from_dpu;
wire [31:0] sram_data_to_dpu;
wire [ 4:0] sram_addr_from_dpu;  
//assign sram_data_in_full = {1'b0, sram_data_in};
assign reset      = ~rst_n;
assign rx_in      = ui_in[3];
assign uio_out[4] = tx_out;
//============================================//
//=================INSTANCES==================//
//============================================//
UARTReceiver UARTReceiver_ins (
    .clk        (clk        ),      // clock
    .reset      (reset      ),    // reset
    .enable     (rx_enable  ),   // enable
    .in         (rx_in      ),       // RX line
    .ready      (rx_ready   ),    // OK to transmit
    .out        (rx_data_out),      // received data
    .valid      (rx_valid   ),    // RX completed
    .error      (uo_out[7]  ),    // frame error
    .overrun    (uo_out[6]  )   // overrun
);

UARTTransmitter UARTTransmitter_ins (
    .clk        (clk        ),   // clock
    .reset      (reset      ),   // reset
    .enable     (tx_enable  ),   // TX enable
    .valid      (tx_valid   ),   // start transaction
    .in         (tx_data_in ),   // data to transmit
    .out        (tx_out     ),   // TX line
    .ready      (tx_ready   )    // ready for TX
);

SRAMController SRAMController_ins (
	.clk           (clk          ),
	.rst_n         (rst_n        ),
	.uart_ready    (uo_out[0]    ),
	// tx 
	.tx_ready      (tx_ready     ),
	.tx_enable     (tx_enable    ),
	.tx_valid      (tx_valid     ), 
	.tx_data_in    (tx_data_in   ),
	// rx
	.rx_data_out   (rx_data_out  ),
	.rx_valid      (rx_valid     ),
	.rx_enable     (rx_enable    ),
	.rx_ready      (rx_ready     ),
	// sram
	.csb_n         (csb_n        ),
	.we_n          (we_n         ),
	.addr          (addr         ),
	//.sram_data_out (sram_data_out_full[31:0]),
	.sram_data_out (sram_data_out),
	.sram_data_in  (sram_data_in ),
	.dpu_load_cmd  (dpu_load_cmd ), // from controller
	.requst_valid  (requst_valid ), // from controller
	.nxt_cmd       (nxt_cmd      ), 
	.sram_data_to_dpu   (sram_data_to_dpu ),
	.sram_data_from_dpu (sram_data_from_dpu),
	.sram_addr_from_dpu (sram_addr_from_dpu)
);

myconfig_sky_dual sram_ins (
`ifdef USE_POWER_PINS
    .vccd1  (VDPWR         ),
    .vssd1  (VGND          ),
`endif		
	.clk0   (clk           ),
	.csb0   (csb_n         ),
	.web0   (we_n          ),
	.addr0  (addr[3:0]     ),
	.din0   (sram_data_in  ),
	.dout0  (sram_data_out ),
	.clk1   (1'b0          ),
	.addr1  (4'b0          ),
	.csb1   (1'b1          ),
	.dout1  ()
);

dpu dpu_ins (
	.clk           (clk               ),
	.rst_n         (rst_n             ),
	//sram controller
	.dpu_load_cmd  (dpu_load_cmd      ), // from controller
	.requst_valid  (requst_valid      ), // from controller
	.nxt_cmd       (nxt_cmd           ), 
	.sram_data_read(sram_data_to_dpu  ),
	.sram_data_out (sram_data_from_dpu),
	.sram_addr     (sram_addr_from_dpu)
);

endmodule
