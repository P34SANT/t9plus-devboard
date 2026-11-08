#
# create_project.tcl - Turnkey Vivado Project Generator for Antminer T9+ Devboard
# Target SoC: Xilinx Zynq-7000 XC7Z010-1CLG400C
#
# Automates 100% of the project creation, Zynq PS7 configuration, AXI GPIO,
# clocking, memory timing, and pin constraints.
#

set script_dir [file normalize [file dirname [info script]]]
set repo_root  [file normalize [file join $script_dir ".."]]
set proj_dir   [file normalize [file join $repo_root "build_vivado"]]
set proj_name  "t9_pynq_base"
set part_name  "xc7z010clg400-1"

puts "==> Creating Vivado Project '$proj_name' in '$proj_dir'..."
create_project -force $proj_name $proj_dir -part $part_name

# Set project properties
set_property target_language Verilog [current_project]
set_property default_lib work [current_project]

# ----------------------------------------------------------------------------
# Create Block Design
# ----------------------------------------------------------------------------
puts "==> Creating Block Design 'design_1'..."
create_bd_design "design_1"

# Instantiate Processing System 7 (Zynq PS)
puts "==> Instantiating and configuring Zynq PS7 block..."
set ps7 [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7 processing_system7_0]

# Configure PS7 for Antminer T9+ Hardware Specifications:
# - DDR3: MT41K128M16 JT-125 (32-bit width, no ECC)
# - CPU: 666.666 MHz, DDR: 533.333 MHz
# - FCLK_CLK0: 100 MHz (AXI Fabric Clock)
# - Peripherals: NAND (MIO 0,2..14), ENET0 Broadcom PHY (MIO 16..27,52..53), SD0 (MIO 40..45), UART1 (MIO 48..49)
set_property -dict [list \
  CONFIG.PCW_PRESET_BANK0_VOLTAGE {LVCMOS 3.3V} \
  CONFIG.PCW_PRESET_BANK1_VOLTAGE {LVCMOS 1.8V} \
  CONFIG.PCW_APU_PERIPHERAL_FREQMHZ {666.666666} \
  CONFIG.PCW_CRYSTAL_PERIPHERAL_FREQMHZ {33.333333} \
  CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {100.000000} \
  CONFIG.PCW_FPGA_FCLK0_ENABLE {1} \
  CONFIG.PCW_USE_M_AXI_GP0 {1} \
  CONFIG.PCW_UIPARAM_DDR_PARTNO {MT41K128M16 JT-125} \
  CONFIG.PCW_UIPARAM_DDR_BUS_WIDTH {32 Bit} \
  CONFIG.PCW_UIPARAM_DDR_MEMORY_TYPE {DDR 3} \
  CONFIG.PCW_UIPARAM_DDR_FREQ_MHZ {533.333333} \
  CONFIG.PCW_NAND_PERIPHERAL_ENABLE {1} \
  CONFIG.PCW_NAND_NAND_IO {MIO 0 2..14} \
  CONFIG.PCW_NAND_GRP_D8_ENABLE {0} \
  CONFIG.PCW_ENET0_PERIPHERAL_ENABLE {1} \
  CONFIG.PCW_ENET0_ENET0_IO {MIO 16 .. 27} \
  CONFIG.PCW_ENET0_GRP_MDIO_ENABLE {1} \
  CONFIG.PCW_ENET0_GRP_MDIO_IO {MIO 52 .. 53} \
  CONFIG.PCW_ENET_RESET_ENABLE {0} \
  CONFIG.PCW_SD0_PERIPHERAL_ENABLE {1} \
  CONFIG.PCW_SD0_SD0_IO {MIO 40 .. 45} \
  CONFIG.PCW_SD0_GRP_CD_ENABLE {0} \
  CONFIG.PCW_SD0_GRP_WP_ENABLE {0} \
  CONFIG.PCW_UART1_PERIPHERAL_ENABLE {1} \
  CONFIG.PCW_UART1_UART1_IO {MIO 48 .. 49} \
  CONFIG.PCW_GPIO_MIO_GPIO_ENABLE {1} \
  CONFIG.PCW_GPIO_MIO_GPIO_IO {MIO} \
] $ps7

# Export Fixed I/O and DDR Interfaces to Top Level
make_bd_intf_pins_external [get_bd_intf_pins processing_system7_0/DDR]
make_bd_intf_pins_external [get_bd_intf_pins processing_system7_0/FIXED_IO]

# ----------------------------------------------------------------------------
# Instantiate Reset Controller & AXI Interconnect
# ----------------------------------------------------------------------------
puts "==> Instantiating Reset Controller and AXI Interconnect..."
set rst_gen [create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset rst_ps7_0_100M]
set axi_ic  [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect ps7_0_axi_periph]
set_property -dict [list CONFIG.NUM_MI {1} CONFIG.NUM_SI {1}] $axi_ic

# ----------------------------------------------------------------------------
# Instantiate AXI GPIO for Onboard User LEDs (Base 0x41200000)
# ----------------------------------------------------------------------------
puts "==> Instantiating AXI GPIO (Channel 1: D5/D6, Channel 2: LED7/LED8)..."
set axi_gpio [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio axi_gpio_0]
set_property -dict [list \
  CONFIG.C_GPIO_WIDTH {2} \
  CONFIG.C_ALL_OUTPUTS {1} \
  CONFIG.C_IS_DUAL {1} \
  CONFIG.C_GPIO2_WIDTH {2} \
  CONFIG.C_ALL_OUTPUTS_2 {1} \
] $axi_gpio

# Create external ports for LEDs
set leds_2bits     [create_bd_port -dir O -from 1 -to 0 leds_2bits]
set leds_ext_2bits [create_bd_port -dir O -from 1 -to 0 leds_ext_2bits]

connect_bd_net [get_bd_pins axi_gpio_0/gpio_io_o] [get_bd_ports leds_2bits]
connect_bd_net [get_bd_pins axi_gpio_0/gpio2_io_o] [get_bd_ports leds_ext_2bits]

# ----------------------------------------------------------------------------
# Connect Clocks and Resets
# ----------------------------------------------------------------------------
puts "==> Wiring AXI Buses, Clocks, and Resets..."
# 100 MHz Fabric Clock
connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] \
               [get_bd_pins processing_system7_0/M_AXI_GP0_ACLK] \
               [get_bd_pins rst_ps7_0_100M/slowest_sync_clk] \
               [get_bd_pins ps7_0_axi_periph/ACLK] \
               [get_bd_pins ps7_0_axi_periph/S00_ACLK] \
               [get_bd_pins ps7_0_axi_periph/M00_ACLK] \
               [get_bd_pins axi_gpio_0/s_axi_aclk]

# Power-on Reset
connect_bd_net [get_bd_pins processing_system7_0/FCLK_RESET0_N] [get_bd_pins rst_ps7_0_100M/ext_reset_in]

# Interconnect & Peripheral Resets
connect_bd_net [get_bd_pins rst_ps7_0_100M/interconnect_aresetn] [get_bd_pins ps7_0_axi_periph/ARESETN]
connect_bd_net [get_bd_pins rst_ps7_0_100M/peripheral_aresetn] \
               [get_bd_pins ps7_0_axi_periph/S00_ARESETN] \
               [get_bd_pins ps7_0_axi_periph/M00_ARESETN] \
               [get_bd_pins axi_gpio_0/s_axi_aresetn]

# Connect AXI GP0 Master -> Interconnect -> AXI GPIO Slave
connect_bd_intf_net [get_bd_intf_pins processing_system7_0/M_AXI_GP0] [get_bd_intf_pins ps7_0_axi_periph/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins ps7_0_axi_periph/M00_AXI] [get_bd_intf_pins axi_gpio_0/S_AXI]

# Assign Memory Address: 0x41200000
assign_bd_address [get_bd_addr_segs {axi_gpio_0/S_AXI/Reg }]
set_property range 4K [get_bd_addr_segs {processing_system7_0/Data/SEG_axi_gpio_0_Reg}]
set_property offset 0x41200000 [get_bd_addr_segs {processing_system7_0/Data/SEG_axi_gpio_0_Reg}]

# Regenerate Layout & Validate Block Design
regenerate_bd_layout
validate_bd_design
save_bd_design

# ----------------------------------------------------------------------------
# Generate Top-Level HDL Wrapper & Add Constraints
# ----------------------------------------------------------------------------
puts "==> Generating HDL Wrapper..."
set bd_file [get_files "design_1.bd"]
set wrapper_path [make_wrapper -files $bd_file -top]
add_files -norecurse $wrapper_path
set_property top design_1_wrapper [current_fileset]
update_compile_order -fileset sources_1

# Add Pin Constraints
puts "==> Adding Master Constraints 't9_v12_pins.xdc'..."
set xdc_file [file normalize [file join $repo_root "constraints" "t9_v12_pins.xdc"]]
add_files -fileset constrs_1 -norecurse $xdc_file
set_property target_constrs_file $xdc_file [current_fileset -constrset]

puts "==> Project creation complete! Ready to synthesize."
