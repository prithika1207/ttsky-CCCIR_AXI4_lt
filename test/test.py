import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

async def axi_write(dut, addr, data):
"""AXI-Lite write using ui_in and uio_in"""


# idle
dut.ui_in.value = 0
dut.uio_in.value = 0
await RisingEdge(dut.clk)

# start write
dut.ui_in.value = (addr << 1) | 0x1
dut.uio_in.value = data
await RisingEdge(dut.clk)

# deassert start
dut.ui_in.value = (addr << 1)

# wait for done
for _ in range(2000):
    val_logic = dut.uo_out.value
    val = int(val_logic) & 1 if val_logic.is_resolvable else 0
    if val:
        return True
    await RisingEdge(dut.clk)

dut._log.error("WRITE timeout ❌")
return False


async def axi_read(dut, addr):
"""AXI-Lite read"""


dut.ui_in.value = 0
await RisingEdge(dut.clk)

# start read
dut.ui_in.value = (addr << 3) | 0x20
await RisingEdge(dut.clk)

# deassert
dut.ui_in.value = (addr << 3)

# wait for done
for _ in range(2000):
    val_logic = dut.uo_out.value
    val = int(val_logic) & 1 if val_logic.is_resolvable else 0
    if val:
        await RisingEdge(dut.clk)
        return int(dut.uio_out.value) & 0xFF
    await RisingEdge(dut.clk)

dut._log.error("READ timeout ❌")
return None


@cocotb.test()
async def axi4lite_test(dut):


# clock
cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

# reset
dut.rst_n.value = 0
dut.ena.value = 1
dut.ui_in.value = 0
dut.uio_in.value = 0

for _ in range(5):
    await RisingEdge(dut.clk)

dut.rst_n.value = 1
await RisingEdge(dut.clk)

dut._log.info("Reset released")

# WRITE
write_addr = 1
write_data = 4

ok = await axi_write(dut, write_addr, write_data)
if not ok:
    return

dut._log.info(f"WRITE DONE addr={write_addr} data={write_data}")

await Timer(20, units="ns")

# READ
read_data = await axi_read(dut, write_addr)
if read_data is None:
    return

dut._log.info(f"READ DONE data={read_data}")

# CHECK
if read_data == write_data:
    dut._log.info("TEST PASSED ✅")
else:
    dut._log.error(f"TEST FAILED ❌ expected={write_data} got={read_data}")
