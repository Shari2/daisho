# SPDX-License-Identifier: BSD-2-Clause
# SPDX-FileCopyrightText: Copyright (c) 2020 Marian Sauer

# Created for ISE version 14.7
set myProject "daisho_usb2_ecm"

project new $myProject

project set family "Spartan6"
project set device "xc6slx45t"
project set package "fgg484"
project set speed "-3"
project set top_level_module_type "HDL"
project set synthesis_tool "XST (VHDL/Verilog)"
project set simulator "ISim (VHDL/Verilog)"
project set "Preferred Language" "VHDL"
project set "Enable Message Filtering" "false"


xfile add "../../../../core/usb2/usb2_crc.v"
xfile add "../../../../core/usb2/usb2_ep.v"
xfile add "../../../../core/usb2/usb2_ep0.v"
xfile add "../../../../core/usb2/usb2_packet.v"
xfile add "../../../../core/usb2/usb2_protocol.v"
xfile add "../../../../core/usb2/usb2_top.v"
xfile add "../../../../core/usb2/usb2_ulpi.v"
xfile add "../../../../core_vhdl/usb2/usb2_descrip_rom.vhd"
xfile add "../../../../core_vhdl/usb2/usb2_ep0in_ram.vhd"
xfile add "../../../../core_vhdl/usb2/usb2_ep_ram.vhd"
xfile add "../constraint/pinout.ucf"
xfile add "../constraint/timing.ucf"
xfile add "../source/sys_pll.vhd"
xfile add "../source/top.vhd"

project set top "Behavioral" "top"

project close
