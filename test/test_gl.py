# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, Timer
from cocotb.utils import get_sim_time
import random

NUM_RUNS_SMOKE = 1
NUM_RUNS_RANDOM = 10
BAUD_ERR_PERCENT = 2

@cocotb.test(timeout_time=50, timeout_unit='sec')
async def run_smoke_case_dpu(dut):
    await reset_project(dut)
    await smoke_case_dpu(dut)

cocotb.test(timeout_time=50, timeout_unit='sec')
async def run_random_case_dpu(dut):
    await reset_project(dut)
    await random_case_dpu(dut)

@cocotb.test(timeout_time=50, timeout_unit='sec')
async def run_smoke_case_uart(dut):
    """TX with randomized payload / clock frequency shift / inter-TX delay."""

    # reset 25 Mhz clock
    await reset_project(dut)
    await somke_case_uart(dut)

@cocotb.test(timeout_time=50, timeout_unit='sec')
async def run_random_case_uart(dut):
    """TX with randomized payload / clock frequency shift / inter-TX delay."""

    # reset 25 Mhz clock
    await reset_project(dut)
    await random_case_uart(dut)

@cocotb.test(timeout_time=50, timeout_unit='sec')
async def run_random_case_full(dut):
     # reset 25 Mhz clock
    await reset_project(dut)
    await random_case_uart(dut)
    await random_case_dpu(dut)
    await random_case_uart(dut)

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
    await ClockCycles(dut.clk, 40)
    
async def write_dpu_cmd(dut, cmd, baud, baud_mult):
    dut._log.info("use dpu")
    TEST_ADDR_LSB = [(cmd >> s) & 1 for s in range(8)]
    # addr write
    for tx_bit in [0] + TEST_ADDR_LSB + [1]:
        current_value = 0b00000000
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        #print("current_value: {0}  tx: {1} i: {2}".format(current_value, tx_bit, i))
        await Timer(int(1 / baud * baud_mult * 1e12), units="ps")
    dut._log.info("dpu cmd finish")

async def write_sram(dut, addr, data_0, data_1, data_2, data_3, baud, baud_mult):
    dut._log.info("write data to sram")
    TEST_ADDR_LSB = [(addr >> s) & 1 for s in range(8)] 
    TEST_DATA_LSB_0 = [(data_0 >> s) & 1 for s in range(8)]
    TEST_DATA_LSB_1 = [(data_1 >> s) & 1 for s in range(8)]
    TEST_DATA_LSB_2 = [(data_2 >> s) & 1 for s in range(8)]
    TEST_DATA_LSB_3 = [(data_3 >> s) & 1 for s in range(8)]
    # addr write
    for tx_bit in [0] + TEST_ADDR_LSB + [1]:
        current_value = 0b00000000
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        #print("current_value: {0}".format(dut.ui_in.value))
        await Timer(int(1 / baud * baud_mult * 1e12), units="ps")
    # wait before data phase
    await Timer(10, units='ms')
    # data write, [0] byte
    for tx_bit in [0] + TEST_DATA_LSB_0 + [1]:
        current_value = 0b00000000
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        await Timer(int(1 / baud * baud_mult * 1e12), units="ps")
    # wait before data phase
    await Timer(10, units='ms')
    # data write, [1] byte
    for tx_bit in [0] + TEST_DATA_LSB_1 + [1]:
        current_value = 0b00000000
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        await Timer(int(1 / baud * baud_mult * 1e12), units="ps")  
        # wait before data phase
    await Timer(10, units='ms')
    # data write, [2] byte
    for tx_bit in [0] + TEST_DATA_LSB_2 + [1]:
        current_value = 0b00000000
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        await Timer(int(1 / baud * baud_mult * 1e12), units="ps")  
    # wait before data phase
    await Timer(10, units='ms')
    # data write, [3] byte
    for tx_bit in [0] + TEST_DATA_LSB_3 + [1]:
        current_value = 0b00000000
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        await Timer(int(1 / baud * baud_mult * 1e12), units="ps")

async def read_sram(dut, addr, baud, baud_mult):
    dut._log.info("read data from sram")   
    TEST_ADDR_LSB = [(addr >> s) & 1 for s in range(8)] 
    # addr write
    for index, tx_bit in enumerate([0] + TEST_ADDR_LSB + [1]):
        current_value = 0b00000000
        current_value |= (tx_bit << 3)
        dut.ui_in.value = current_value 
        if index < len(TEST_ADDR_LSB) + 1:
            await Timer(int(1 / baud * baud_mult * 1e12), units="ps")

async def check_data(dut, data_write_0, data_write_1, data_write_2, data_write_3, baud, baud_mult):
    dut._log.info("check the data that was written in sram")
    TEST_DATA_LSB_0 = [(data_write_0 >> s) & 1 for s in range(8)]
    TEST_DATA_LSB_1 = [(data_write_1 >> s) & 1 for s in range(8)]
    TEST_DATA_LSB_2 = [(data_write_2 >> s) & 1 for s in range(8)]
    TEST_DATA_LSB_3 = [(data_write_3 >> s) & 1 for s in range(8)]
    #i = 0
    uart_instance = getattr(dut.user_project, r"\UARTTransmitter_ins.out")
    await FallingEdge(uart_instance)
    # make sure signal is stable
    await Timer(int(0.5 / baud * baud_mult * 1e12), units="ps")
    # check every bit of received data 0
    for expected_bit in [0] + TEST_DATA_LSB_0 + [1]:
        #dut._log.info("i -> {0}".format(i))
        #dut._log.info(f"current simulation time: {get_sim_time(units='ns')} ns")
        assert uart_instance.value == expected_bit
        #i = i + 1
        #print("dut_value.out->{0}".format(dut.user_project.UARTTransmitter_ins.out.value))
        #print("expected_value->{0}".format(expected_bit))
        await Timer(int(1.0 / baud * baud_mult * 1e12), units="ps")
    await FallingEdge(uart_instance)
    # make sure signal is stable
    await Timer(int(0.5 / baud * baud_mult * 1e12), units="ps")
    # check every bit of received data 1
    for expected_bit in [0] + TEST_DATA_LSB_1 + [1]:
        assert uart_instance.value == expected_bit
        await Timer(int(1.0 / baud * baud_mult * 1e12), units="ps")
    await FallingEdge(uart_instance)
    # make sure signal is stable
    await Timer(int(0.5 / baud * baud_mult * 1e12), units="ps")
    # check every bit of received data 2
    for expected_bit in [0] + TEST_DATA_LSB_2 + [1]:
        assert uart_instance.value == expected_bit
        await Timer(int(1.0 / baud * baud_mult * 1e12), units="ps")
    await FallingEdge(uart_instance)
    # make sure signal is stable
    await Timer(int(0.5 / baud * baud_mult * 1e12), units="ps")
    # check every bit of received data 3
    for expected_bit in [0] + TEST_DATA_LSB_3 + [1]:
        assert uart_instance.value == expected_bit
        await Timer(int(1.0 / baud * baud_mult * 1e12), units="ps")
    dut._log.info("CASE PASS")

async def smoke_case_dpu(dut):
    # carry out 100 transmissions, only add, no overflow
    for count in range(NUM_RUNS_SMOKE):
        
        # addr
        ADDR_BYTE_CMD = 0b00000000 # write sram
        # randomized data
        DATA_BYTE_0 = random.randint(1,254)
        DATA_BYTE_1 = random.randint(1,255)
        DATA_BYTE_2 = random.randint(1,255)
        DATA_BYTE_3 = random.randint(1,255) 
        print("data0-{0}".format(DATA_BYTE_0))
        print("data1-{0}".format(DATA_BYTE_1))
        print("data2-{0}".format(DATA_BYTE_2))
        print("data3-{0}".format(DATA_BYTE_3))
        # randomized baud multiplier (+/- 2%)
        baud_mult = 1.0 + (random.random() - 0.5) / 50 * BAUD_ERR_PERCENT
        
         # write into sram
        await write_sram(dut, ADDR_BYTE_CMD, DATA_BYTE_0, DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 9600, baud_mult)
        await Timer(10, units='ms')  
    
         # activate dpu
        ADDR_BYTE_CMD = 0b10000000
        await write_dpu_cmd(dut, ADDR_BYTE_CMD, 9600, baud_mult)
        await Timer(10, units='ms')
        # read from sram
        ADDR_BYTE_CMD = 0b00100000
        await read_sram(dut, ADDR_BYTE_CMD, 9600, baud_mult)
        
         # check the result
        await check_data(dut, (DATA_BYTE_0 + 1), DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 9600, baud_mult)
        # randomized inter-TX interval
        await Timer(10, units='ms')
        if random.random() > 0.1:
            await Timer(random.randint(1,2000), units='ns')  
    
async def random_case_dpu(dut):
    # carry out 100 transmissions
    for count in range(NUM_RUNS_RANDOM):
        
        # addr
        ADDR_BYTE_CMD = random.randint(0,15) # write sram
        # randomized data
        DATA_BYTE_0 = random.randint(0,255)
        DATA_BYTE_1 = random.randint(0,255)
        DATA_BYTE_2 = random.randint(0,255)
        DATA_BYTE_3 = random.randint(0,255) 
        print("data0-{0}".format(DATA_BYTE_0))
        print("data1-{0}".format(DATA_BYTE_1))
        print("data2-{0}".format(DATA_BYTE_2))
        print("data3-{0}".format(DATA_BYTE_3))
        data_32bit = (DATA_BYTE_3 << 24) | (DATA_BYTE_2 << 16) | (DATA_BYTE_1 << 8) | DATA_BYTE_0
        print(f"Original 32-bit integer: {data_32bit:#010x}")
        # randomized baud multiplier (+/- 2%)
        baud_mult = 1.0 + (random.random() - 0.5) / 50 * BAUD_ERR_PERCENT
        
        # write into sram
        await write_sram(dut, ADDR_BYTE_CMD, DATA_BYTE_0, DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 9600, baud_mult)
        await Timer(10, units='ms')  
    
         # activate dpu
        ADDR_BYTE_CMD_DPU = ADDR_BYTE_CMD | (1 << 7) # set[7] = 1
        new_bits = random.randint(0, 3)
        ADDR_BYTE_CMD_DPU = (ADDR_BYTE_CMD_DPU & 0b10011111) | (new_bits << 5)
        await write_dpu_cmd(dut, ADDR_BYTE_CMD_DPU, 9600, baud_mult)
        await Timer(10, units='ms')

        # check according to the situation
        if (new_bits == 0):# add
            # read from sram
            ADDR_BYTE_CMD |= (1 << 5) # set ADDR_BYTE_CMD[5] = 1, so we could read
            data_32bit = (data_32bit + 1) & 0xFFFFFFFF
            # the correct data that expected
            DATA_BYTE_3 = (data_32bit >> 24) & 0xFF
            DATA_BYTE_2 = (data_32bit >> 16) & 0xFF
            DATA_BYTE_1 = (data_32bit >> 8) & 0xFF
            DATA_BYTE_0 = data_32bit & 0xFF
            print("data0-{0}".format(DATA_BYTE_0))
            print("data1-{0}".format(DATA_BYTE_1))
            print("data2-{0}".format(DATA_BYTE_2))
            print("data3-{0}".format(DATA_BYTE_3))
            await read_sram(dut, ADDR_BYTE_CMD, 9600, baud_mult)
        
            # check the result
            await check_data(dut, DATA_BYTE_0, DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 9600, baud_mult)
            # randomized inter-TX interval
            await Timer(10, units='ms')
            if random.random() > 0.1:
                await Timer(random.randint(1,2000), units='ns')  
        elif (new_bits == 1):# sub
            # read from sram
            ADDR_BYTE_CMD |= (1 << 5) # set ADDR_BYTE_CMD[5] = 1, so we could read
            data_32bit = (data_32bit - 1) & 0xFFFFFFFF
            # the correct data that expected
            DATA_BYTE_3 = (data_32bit >> 24) & 0xFF
            DATA_BYTE_2 = (data_32bit >> 16) & 0xFF
            DATA_BYTE_1 = (data_32bit >> 8) & 0xFF
            DATA_BYTE_0 = data_32bit & 0xFF
            print("data0-{0}".format(DATA_BYTE_0))
            print("data1-{0}".format(DATA_BYTE_1))
            print("data2-{0}".format(DATA_BYTE_2))
            print("data3-{0}".format(DATA_BYTE_3))
            await read_sram(dut, ADDR_BYTE_CMD, 9600, baud_mult)
        
            # check the result
            await check_data(dut, DATA_BYTE_0, DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 9600, baud_mult)
            # randomized inter-TX interval
            await Timer(10, units='ms')
            if random.random() > 0.1:
                await Timer(random.randint(1,2000), units='ns')  
        elif (new_bits == 2):# mul
            # read from sram
            ADDR_BYTE_CMD |= (1 << 5) # set ADDR_BYTE_CMD[5] = 1, so we could read
            data_32bit = (data_32bit << 1) & 0xFFFFFFFF
            # the correct data that expected
            DATA_BYTE_3 = (data_32bit >> 24) & 0xFF
            DATA_BYTE_2 = (data_32bit >> 16) & 0xFF
            DATA_BYTE_1 = (data_32bit >> 8) & 0xFF
            DATA_BYTE_0 = data_32bit & 0xFF
            print("data0-{0}".format(DATA_BYTE_0))
            print("data1-{0}".format(DATA_BYTE_1))
            print("data2-{0}".format(DATA_BYTE_2))
            print("data3-{0}".format(DATA_BYTE_3))
            await read_sram(dut, ADDR_BYTE_CMD, 9600, baud_mult)
        
            # check the result
            await check_data(dut, DATA_BYTE_0, DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 9600, baud_mult)
            # randomized inter-TX interval
            await Timer(10, units='ms')
            if random.random() > 0.1:
                await Timer(random.randint(1,2000), units='ns') 
        else: # new_bits == 3:# div
            # read from sram
            ADDR_BYTE_CMD |= (1 << 5) # set ADDR_BYTE_CMD[5] = 1, so we could read
            data_32bit = (data_32bit >> 1) & 0xFFFFFFFF
            # the correct data that expected
            DATA_BYTE_3 = (data_32bit >> 24) & 0xFF
            DATA_BYTE_2 = (data_32bit >> 16) & 0xFF
            DATA_BYTE_1 = (data_32bit >> 8) & 0xFF
            DATA_BYTE_0 = data_32bit & 0xFF
            print("data0-{0}".format(DATA_BYTE_0))
            print("data1-{0}".format(DATA_BYTE_1))
            print("data2-{0}".format(DATA_BYTE_2))
            print("data3-{0}".format(DATA_BYTE_3))
            await read_sram(dut, ADDR_BYTE_CMD, 9600, baud_mult)
        
            # check the result
            await check_data(dut, DATA_BYTE_0, DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 9600, baud_mult)
            # randomized inter-TX interval
            await Timer(10, units='ms')
            if random.random() > 0.1:
                await Timer(random.randint(1,2000), units='ns') 
    
async def somke_case_uart(dut):
    # carry out 100 transmissions
    for count in range(NUM_RUNS_SMOKE):
        
        # addr
        ADDR_BYTE_CMD = 0b00000110 # write sram
        # randomized data
        DATA_BYTE_0 = random.randint(0,255)
        DATA_BYTE_1 = random.randint(0,255)
        DATA_BYTE_2 = random.randint(0,255)
        DATA_BYTE_3 = random.randint(0,255) 
        print("data0-{0}".format(DATA_BYTE_0))
        print("data1-{0}".format(DATA_BYTE_1))
        print("data2-{0}".format(DATA_BYTE_2))
        print("data3-{0}".format(DATA_BYTE_3))
        # randomized baud multiplier (+/- 2%)
        baud_mult = 1.0 + (random.random() - 0.5) / 50 * BAUD_ERR_PERCENT
        
        # write into sram
        await write_sram(dut, ADDR_BYTE_CMD, DATA_BYTE_0, DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 9600, baud_mult)
        await Timer(10, units='ms')
        
        # read from sram
        ADDR_BYTE_CMD = 0b00100110
        await read_sram(dut, ADDR_BYTE_CMD, 9600, baud_mult)
        
        # check the result
        await check_data(dut, DATA_BYTE_0, DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 9600, baud_mult)
        # randomized inter-TX interval
        await Timer(10, units='ms')
        if random.random() > 0.1:
            await Timer(random.randint(1,2000), units='ns')   
    
async def random_case_uart(dut):
    # carry out 100 transmissions
    for count in range(NUM_RUNS_RANDOM):
        
        # addr
        ADDR_BYTE_CMD = random.randint(0,15) # write sram
        # randomized data
        DATA_BYTE_0 = random.randint(0,255)
        DATA_BYTE_1 = random.randint(0,255)
        DATA_BYTE_2 = random.randint(0,255)
        DATA_BYTE_3 = random.randint(0,255) 
        print("data0-{0}".format(DATA_BYTE_0))
        print("data1-{0}".format(DATA_BYTE_1))
        print("data2-{0}".format(DATA_BYTE_2))
        print("data3-{0}".format(DATA_BYTE_3))
        # randomized baud multiplier (+/- 2%)
        baud_mult = 1.0 + (random.random() - 0.5) / 50 * BAUD_ERR_PERCENT
        
        # write into sram
        await write_sram(dut, ADDR_BYTE_CMD, DATA_BYTE_0, DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 9600, baud_mult)
        await Timer(10, units='ms')
        
        # read from sram
        ADDR_BYTE_CMD |= (1 << 5) # set ADDR_BYTE_CMD[5] = 1, so we could read
        await read_sram(dut, ADDR_BYTE_CMD, 9600, baud_mult)
        
        # check the result
        await check_data(dut, DATA_BYTE_0, DATA_BYTE_1, DATA_BYTE_2, DATA_BYTE_3, 9600, baud_mult)
        # randomized inter-TX interval
        await Timer(10, units='ms')
        if random.random() > 0.1:
            await Timer(random.randint(1,2000), units='ns')
    

    
    
    
    

    
    
    
