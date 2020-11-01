SPDX-License-Identifier: BSD-2-Clause

SPDX-FileCopyrightText: Copyright (c) 2020 Marian Sauer

# Goal
Implement a real world use case USB-to-Ethernet device on an FPGA and learn
something.


> "Complications arose, ensued, were overcome"
>
> -- Captain Jack Sparrow


# What to expect
Nothing really. This is a **personal**, one person, open source project worked
on/maintained in **spare time**. See license details.

# Contact
Project home is https://github.com/Shari2/daisho_usb2_ecm

# Milestones
1. USB 2.0 Full-speed only device enumeration with Linux xHCI Host
2. USB 2.0 High-speed device enumeration with Linux xHCI Host
3. Windows USBCV Test
4. Implement Full-speed USB-to-Ethernet
   (ECM function, 12 Mbit/s half duplex vs 10 Mbit/s full duplex)
5. Cover USB 2.0 Full-speed device standard requirements or document violations
6. Implement High-speed USB-to-Ethernet
   (ECM function, 480 Mbit/s half duplex vs 100 Mbit/s full duplex)
7. Cover USB 2.0 High-speed device standard requirements or document violations

# Why Numato Opsis hardware?
- No external Phy board required (ULPI Phy and RGMII Phy connected to FPGA)
- Interfaces to implement real USB functions
 - RGMII Phy for CDC ECM or CDC NCM function
 - HDMI input for Audio/Video function
 - SD Card for Mass Storage function
- FOSS Hardware

# Why Daisho USB 2.0 Device IP core?
- Simplified BSD license
- No softcpu + software needed to operate
- Offers progression path to USB 3.0 device

# Why no USB 3.0 support?
- USB 2.0 device standard compatibility is enough work
- No hardware to test it on (a untested function is just maintenance overhead)

# Risks trying to reproduce/reuse this project
- Numato Opsis hardware appears to be End-of-life (last checked 2020-11-02)
- FPGA is only supported by older vendor tools
- Vendor lock-in by using FPGA vendor specific components
- Vendor lock-in by using Phy specific datasheets

# Standards to respect for compatibility/portability/interoperability
- ULPI Revision 1.1 October 20, 2004 (fallback is the specific ULPI Phy datasheet)
- RGMII Version 2.0 4/1/2002 (fallback is the specific RGMII Phy datasheet)
- USB Revision 2.0 April 27, 2000 (usb.org)
- USB CDC Revision 1.2 December 6, 2012 (usb.org)
- USB CDC ECM Revision 1.2 December 6, 2012 (usb.org)
- IEEE Std 802.3-2018 (ieee.org)

# Other Resources

[Daisho USB IP ported to Xilinx FPGA](https://github.com/enjoy-digital/daisho)

[Daisho project](https://github.com/mossmann/daisho)

[Numato Opsis hardware](https://numato.com/product/numato-opsis-fpga-based-open-video-platform/)

[Other projects on Numato Opsis hardware](https://hdmi2usb.tv/numato-opsis/)
