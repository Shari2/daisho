# SPDX-License-Identifier: BSD-2-Clause
# SPDX-FileCopyrightText: Copyright (c) 2020 Marian Sauer


# usage:
#
# cmake -H. -Bbuild -GNinja
#
# ninja -C build/ generate_descriptor_set
#
# ninja -C build/ load_to_fpga

cmake_minimum_required(VERSION 3.16)
project(daisho_descriptor_set_gen)

add_executable(usb_descrip_gen "core/usb_descrip_gen.c")
target_link_libraries(usb_descrip_gen PRIVATE m)

add_custom_target(generate_descriptor_set
  COMMAND $<TARGET_FILE:usb_descrip_gen>
  WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}/core"
)

# openocd via flyswatter2 jtag connected to numato opsis
add_custom_target(load_to_fpga
  COMMAND openocd -f "${PROJECT_SOURCE_DIR}/board/numato_opsis/numato_opsis.cfg" -c \"init\; xc6s_print_dna xc6s.tap\; pld load 0  "${PROJECT_SOURCE_DIR}/board/numato_opsis/ise_project/daisho_usb2_ecm/top.bit" \; reset halt\; exit\"
)

# usage with ise environment:
#  . <install_dir>/Xilinx/14.7/ISE_DS/settings64.sh
# LD_LIBRARY_PATH="" cmake -H. -Bbuild -GNinja
# LD_LIBRARY_PATH="" ninja -C build/ generate_ise_project
#

add_custom_target(generate_ise_project
  COMMAND xtclsh "${PROJECT_SOURCE_DIR}/board/numato_opsis/ise_project/daisho_usb2_ecm/daisho_usb2_ecm.tcl"
  WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}/board/numato_opsis/ise_project/daisho_usb2_ecm"
  DEPENDS generate_descriptor_set
)
