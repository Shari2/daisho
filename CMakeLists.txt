# SPDX-License-Identifier: BSD-2-Clause
# SPDX-FileCopyrightText: Copyright (c) 2020 Marian Sauer


# usage:
#
# cmake -H. -Bbuild -GNinja
# ninja -C build/ generate_descriptor_set


cmake_minimum_required(VERSION 3.16)
project(daisho_descriptor_set_gen)

add_executable(usb_descrip_gen "core/usb_descrip_gen.c")
target_link_libraries(usb_descrip_gen PRIVATE m)

add_custom_target(generate_descriptor_set
  COMMAND $<TARGET_FILE:usb_descrip_gen>
  WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}/core"
)
