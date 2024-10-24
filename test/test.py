# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Edge, Timer
import random

NUM_RUNS = 1
BAUD_ERR_PERCENT = 2

@cocotb.test(timeout_time=50, timeout_unit='sec')
async def run_random_case(dut):
    """TX with randomized payload / clock frequency shift / inter-TX delay."""

    # reset 25 Mhz clock
    await reset_project(dut)

    # carry out 100 transmissions
    for count in range(NUM_RUNS):
        
		# addr
        ADDR_BYTE_CMD = 0b00000000 # write sram
        # randomized data
        DATA_BYTE_0 = random.randint(0,255)
        DATA_BYTE_1 = random.randint(0,255)
        DATA_BYTE_2 = random.randint(0,255)
        DATA_BYTE_3 = random.randint(0,255) 

        # randomized baud multiplier (+/- 2%)
        baud_mult = 1.0 + (random.random() - 0.5) / 50 * BAUD_ERR_PERCENT
        
		# write into sram
        await write_sram(dut, ADDR_BYTE_CMD, DATA_BYTE_0, DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 115200, baud_mult)
        await Timer(10, units='ms')
        
		# read from sram
        await read_sram(dut, ADDR_BYTE_CMD, 115200, baud_mult)
        
		# check the result
        await check_data(dut, DATA_BYTE_0, DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 115200, baud_mult)
        # randomized inter-TX interval
        await Timer(10, units='ms')
        if random.random() > 0.1:
            await Timer(random.randint(1,2000), units='ns')
            
# --- HELPER FUNCTIONS ---
async def reset_project(dut):
    dut._log.info("Start")

    # Set the clock period to 40 ns (25 MHz)
    clock = Clock(dut.clk, 40, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0b00001000
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 20)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 20)
    
async def write_sram(dut, addr, data_0, data_1, data_2, data_3, baud, baud_mult):
    dut._log.info("write data to sram")
    TEST_ADDR_LSB = [(addr >> s) & 1 for s in range(8)] 
    TEST_DATA_LSB_0 = [(data_0 >> s) & 1 for s in range(8)]
    TEST_DATA_LSB_1 = [(data_1 >> s) & 1 for s in range(8)]
    TEST_DATA_LSB_2 = [(data_2 >> s) & 1 for s in range(8)]
    TEST_DATA_LSB_3 = [(data_3 >> s) & 1 for s in range(8)]
    # addr write
    for tx_bit in [0] + TEST_ADDR_LSB + [1]:
        current_value = dut.ui_in.value
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        await Timer(int(1 / baud * baud_mult * 1e12), units="ps")
    # wait before data phase
    await Timer(10, units='ms')
    # data write, [0] byte
    for tx_bit in [0] + TEST_DATA_LSB_0 + [1]:
        current_value = dut.ui_in.value
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        await Timer(int(1 / baud * baud_mult * 1e12), units="ps")
    # wait before data phase
    await Timer(10, units='ms')
    # data write, [1] byte
    for tx_bit in [0] + TEST_DATA_LSB_1 + [1]:
        current_value = dut.ui_in.value
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        await Timer(int(1 / baud * baud_mult * 1e12), units="ps")  
        # wait before data phase
    await Timer(10, units='ms')
    # data write, [2] byte
    for tx_bit in [0] + TEST_DATA_LSB_2 + [1]:
        current_value = dut.ui_in.value
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        await Timer(int(1 / baud * baud_mult * 1e12), units="ps")  
    # wait before data phase
    await Timer(10, units='ms')
    # data write, [3] byte
    for tx_bit in [0] + TEST_DATA_LSB_3 + [1]:
        current_value = dut.ui_in.value
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        await Timer(int(1 / baud * baud_mult * 1e12), units="ps")

async def read_sram(dut, addr, baud, baud_mult):
    dut._log.info("read data from sram")   
    TEST_ADDR_LSB = [(addr >> s) & 1 for s in range(8)] 
    # addr write
    for tx_bit in [0] + TEST_ADDR_LSB + [1]:
        current_value = dut.ui_in.value
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        await Timer(int(1 / baud * baud_mult * 1e12), units="ps")

async def check_data(dut, data_write_0, data_write_1, data_write_2, data_write_3, baud, baud_mult):
    dut._log.info("check the data that was written in sram")
    TEST_DATA_LSB_0 = [(data_write_0 >> s) & 1 for s in range(8)]
    TEST_DATA_LSB_1 = [(data_write_1 >> s) & 1 for s in range(8)]
    TEST_DATA_LSB_2 = [(data_write_2 >> s) & 1 for s in range(8)]
    TEST_DATA_LSB_3 = [(data_write_3 >> s) & 1 for s in range(8)]
    assert dut.user_project.UARTTransmitter_ins.out.value == 1
    await Edge(dut.user_project.UARTTransmitter_ins.out)
    # make sure signal is stable
    await Timer(int(0.5 / baud * baud_mult * 1e12), units="ps")
    # check every bit of received data 0
    for expected_bit in [0] + TEST_DATA_LSB_0 + [1]:
        assert dut.user_project.UARTTransmitter_ins.out.value == expected_bit
        await Timer(int(1.0 / baud * baud_mult * 1e12), units="ps")
    await Edge(dut.user_project.UARTTransmitter_ins.out)
    # make sure signal is stable
    await Timer(int(0.5 / baud * baud_mult * 1e12), units="ps")
    # check every bit of received data 1
    for expected_bit in [0] + TEST_DATA_LSB_1 + [1]:
        assert dut.user_project.UARTTransmitter_ins.out.value == expected_bit
        await Timer(int(1.0 / baud * baud_mult * 1e12), units="ps")
    await Edge(dut.user_project.UARTTransmitter_ins.out)
    # make sure signal is stable
    await Timer(int(0.5 / baud * baud_mult * 1e12), units="ps")
    # check every bit of received data 2
    for expected_bit in [0] + TEST_DATA_LSB_2 + [1]:
        assert dut.user_project.UARTTransmitter_ins.out.value == expected_bit
        await Timer(int(1.0 / baud * baud_mult * 1e12), units="ps")
    await Edge(dut.user_project.UARTTransmitter_ins.out)
    # make sure signal is stable
    await Timer(int(0.5 / baud * baud_mult * 1e12), units="ps")
    # check every bit of received data 3
    for expected_bit in [0] + TEST_DATA_LSB_3 + [1]:
        assert dut.user_project.UARTTransmitter_ins.out.value == expected_bit
        await Timer(int(1.0 / baud * baud_mult * 1e12), units="ps")
    dut._log.info("CASE PASS")

    

    
    
    
    

    
    
    
