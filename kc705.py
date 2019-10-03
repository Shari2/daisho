#!/usr/bin/env python3

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.fhdl.specials import Tristate

from litex.build.generic_platform import *

from litex.soc.interconnect.csr import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.uart import UARTWishboneBridge

from liteeth.common import convert_ip
from liteeth.phy import LiteEthPHY
from liteeth.core import LiteEthUDPIPCore
from liteeth.frontend.etherbone import LiteEthEtherbone

from litex.boards.platforms import kc705

from litescope import LiteScopeAnalyzer


_usb3_io = [
    # HiTechGlobal USB3.0 FMC P1 connector
    ("usb_clkout", 0, Pins("HPC:LA00_CC_P"), IOStandard("LVCMOS25")),
    ("usb_reset_n", 0, Pins("HPC:LA32_N"), IOStandard("LVCMOS25")),
    ("usb_ulpi", 0,
        Subsignal("clk", Pins("HPC:HA01_CC_P")),
        Subsignal("data", Pins(
            "HPC:HA11_N", "HPC:HA13_N", "HPC:HA15_N", "HPC:HA12_N",
            "HPC:HA14_N", "HPC:HA15_P", "HPC:HA16_P", "HPC:HA12_P")),
        Subsignal("dir", Pins("HPC:HA14_P")),
        Subsignal("stp", Pins("HPC:HA16_N")),
        Subsignal("nxt", Pins("HPC:HA13_P")),
        IOStandard("LVCMOS25"),
    ),
    ("usb_pipe_ctrl", 0,
        Subsignal("phy_reset_n", Pins("HPC:LA12_P")),
        Subsignal("tx_detrx_lpbk", Pins("HPC:LA29_N")),
        Subsignal("tx_elecidle", Pins("HPC:LA27_P")),
        Subsignal("power_down", Pins("HPC:LA12_N", "HPC:LA13_P")),
        Subsignal("tx_oneszeros", Pins("HPC:LA27_N")),
        Subsignal("tx_deemph", Pins("HPC:LA31_P", "HPC:LA28_N")),
        Subsignal("tx_margin", Pins("HPC:LA31_N", "HPC:LA30_P", "HPC:LA30_N")),
        Subsignal("tx_swing", Pins("HPC:LA29_P")),
        Subsignal("rx_polarity", Pins("HPC:LA16_N")),
        Subsignal("rx_termination", Pins("HPC:LA13_N")),
        Subsignal("rate", Pins("HPC:LA28_P")),
        Subsignal("elas_buf_mode", Pins("HPC:LA15_N")),
        IOStandard("LVCMOS25"),
    ),
    ("usb_pipe_status", 0,
        Subsignal("rx_elecidle", Pins("HPC:LA11_N")),
        Subsignal("rx_status", Pins("HPC:LA14_P", "HPC:LA15_P", "HPC:LA14_N")),
        Subsignal("phy_status", Pins("HPC:LA16_P")),
        Subsignal("pwr_present", Pins("HPC:LA32_P")),
        IOStandard("LVCMOS25"),
    ),
    ("usb_pipe_data", 0,
        Subsignal("rx_clk", Pins("HPC:LA01_CC_P")),
        Subsignal("rx_valid", Pins("HPC:LA11_P")),
        Subsignal("rx_data", Pins(
            "HPC:LA10_N", "HPC:LA10_P", "HPC:LA09_N", "HPC:LA09_P",
            "HPC:LA07_N", "HPC:LA08_N", "HPC:LA05_N", "HPC:LA03_N",
            "HPC:LA06_N", "HPC:LA02_P", "HPC:LA06_P", "HPC:LA04_P",
            "HPC:LA03_P", "HPC:LA08_P", "HPC:LA07_P", "HPC:LA04_N")),
        Subsignal("rx_datak", Pins("HPC:LA02_N", "HPC:LA05_P")),

        Subsignal("tx_clk", Pins("HPC:LA20_P")),
        Subsignal("tx_data", Pins(
            "HPC:LA24_N", "HPC:LA26_N", "HPC:LA24_P", "HPC:LA26_P",
            "HPC:LA25_N", "HPC:LA21_N", "HPC:LA25_P", "HPC:LA21_P",
            "HPC:LA22_P", "HPC:LA22_N", "HPC:LA19_N", "HPC:LA23_N",
            "HPC:LA23_P", "HPC:LA18_CC_P", "HPC:LA19_P", "HPC:LA20_N")),
        Subsignal("tx_datak", Pins("HPC:LA18_CC_N", "HPC:LA17_CC_P")),
        IOStandard("LVCMOS25"),
    ),
]


class Platform(kc705.Platform):
    def __init__(self, *args, **kwargs):
        kc705.Platform.__init__(self, *args, **kwargs)
        self.add_extension(_usb3_io)


class BaseSoC(SoCCore):
    csr_map = {
        "eth_phy":  11,
        "eth_core": 12
    }
    csr_map.update(SoCCore.csr_map)
    def __init__(self, platform,
        mac_address=0x10e2d5000000,
        ip_address="192.168.1.50"):
        clk_freq = int(1e9/platform.default_clk_period)
        SoCCore.__init__(self, platform, clk_freq,
            cpu_type=None,
            csr_data_width=32,
            with_uart=False,
            ident="Daisho USB3.0 Test Design",
            with_timer=False
        )
        self.submodules.crg = CRG(platform.request(platform.default_clk_name))

        # uart <--> wishbone
        self.add_cpu_or_bridge(UARTWishboneBridge(platform.request("serial"),
                                                  clk_freq, baudrate=115200))
        self.add_wb_master(self.cpu_or_bridge.wishbone)

        # ethernet PHY and UDP/IP stack
        self.submodules.eth_phy = LiteEthPHY(platform.request("eth_clocks"),
                                             platform.request("eth"),
                                             clk_freq=clk_freq)
        self.submodules.eth_core = LiteEthUDPIPCore(self.eth_phy,
                                                    mac_address,
                                                    convert_ip(ip_address),
                                                    clk_freq)

        # ethernet <--> wishbone
        self.submodules.etherbone = LiteEthEtherbone(self.eth_core.udp, 1234)
        self.add_wb_master(self.etherbone.wishbone.bus)

        # timing constraints
        self.crg.cd_sys.clk.attr.add("keep")
        self.eth_phy.crg.cd_eth_rx.clk.attr.add("keep")
        self.eth_phy.crg.cd_eth_tx.clk.attr.add("keep")
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 6.0)
        self.platform.add_period_constraint(self.eth_phy.crg.cd_eth_rx.clk, 8.0)
        self.platform.add_period_constraint(self.eth_phy.crg.cd_eth_tx.clk, 8.0)

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.eth_phy.crg.cd_eth_rx.clk,
            self.eth_phy.crg.cd_eth_tx.clk)


class USBSoC(BaseSoC):
    csr_map = {
        "analyzer": 20,
        "usb2_control": 21,
        "usb3_control": 22
    }
    csr_map.update(BaseSoC.csr_map)
    def __init__(self, platform, usb_connector=0,
        with_usb2=True, with_usb2_analyzer=False,
        with_usb3=True, with_usb3_analyzer=False):
        BaseSoC.__init__(self, platform)

        # usb ios
        usb_reset_n = platform.request("usb_reset_n", usb_connector)
        if with_usb2:
            usb_ulpi = platform.request("usb_ulpi", usb_connector)
        if with_usb3:
            usb_pipe_ctrl = platform.request("usb_pipe_ctrl", usb_connector)
            usb_pipe_status = platform.request("usb_pipe_status", usb_connector)
            usb_pipe_data = platform.request("usb_pipe_data", usb_connector)

        usb2_reset_n = Signal(reset=1)
        usb3_reset_n = Signal(reset=1)
        self.comb += usb_reset_n.eq(usb2_reset_n & usb3_reset_n)

        # usb2 core
        if with_usb2:
            class USB2Control(Module, AutoCSR):
                def __init__(self):
                    self._phy_enable = CSRStorage()
                    self._core_enable = CSRStorage()

                    # probably not working but prevent synthesis optimizations
                    self._buf_in_addr = CSRStorage(9)
                    self._buf_in_data = CSRStorage(8)
                    self._buf_in_wren = CSR()
                    self._buf_in_ready = CSRStatus()
                    self._buf_in_commit = CSR()
                    self._buf_in_commit_len = CSRStorage(10)
                    self._buf_in_commit_ack = CSRStatus()

                    self._buf_out_addr = CSRStorage(9)
                    self._buf_out_q = CSRStatus(8)
                    self._buf_out_len = CSRStatus(10)
                    self._buf_out_hasdata = CSRStatus()
                    self._buf_out_arm = CSR()
                    self._buf_out_arm_ack = CSRStatus()

                    # # #

                    self.phy_enable = self._phy_enable.storage
                    self.core_enable = self._core_enable.storage

                    self.buf_in_addr = self._buf_in_addr.storage
                    self.buf_in_data = self._buf_in_data.storage
                    self.buf_in_wren = self._buf_in_wren.re & self._buf_in_wren.r
                    self.buf_in_ready = self._buf_in_ready.status
                    self.buf_in_commit = self._buf_in_commit.re & self._buf_in_commit.r
                    self.buf_in_commit_len = self._buf_in_commit_len.storage
                    self.buf_in_commit_ack = self._buf_in_commit_ack.status

                    self.buf_out_addr = self._buf_out_addr.storage
                    self.buf_out_q = self._buf_out_q.status
                    self.buf_out_len = self._buf_out_len.status
                    self.buf_out_hasdata = self._buf_out_hasdata.status
                    self.buf_out_arm = self._buf_out_arm.re & self._buf_out_arm.r
                    self.buf_out_arm_ack = self._buf_out_arm_ack.status


            self.submodules.usb2_control = USB2Control()

            self.clock_domains.cd_ulpi = ClockDomain()
            self.comb += self.cd_ulpi.clk.eq(usb_ulpi.clk)

            self.cd_ulpi.clk.attr.add("keep")
            self.platform.add_period_constraint(self.cd_ulpi.clk, 16.667)
            self.platform.add_false_path_constraints(
                self.crg.cd_sys.clk,
                self.cd_ulpi.clk)


            stat_connected = Signal()
            stat_fs = Signal()
            stat_hs = Signal()
            stat_configured = Signal()

            vend_req_act = Signal()
            vend_req_request = Signal(8)
            vend_req_val = Signal(16)

            err_crc_pid = Signal()
            err_crc_tok = Signal()
            err_crc_pkt = Signal()
            err_pid_out_of_seq = Signal()
            err_setup_pkt = Signal()

            dbg_frame_num = Signal(11)
            dbg_linestate = Signal(2)

            self.comb += usb2_reset_n.eq(self.usb2_control.phy_enable)
            self.specials += Instance("usb2_top",
                i_ext_clk=ClockSignal(),
                i_reset_n=self.usb2_control.core_enable,
                #o_reset_n_out=,

                i_phy_ulpi_clk=usb_ulpi.clk,
                io_phy_ulpi_d=usb_ulpi.data,
                i_phy_ulpi_dir=usb_ulpi.dir,
                o_phy_ulpi_stp=usb_ulpi.stp,
                i_phy_ulpi_nxt=usb_ulpi.nxt,

                i_opt_disable_all=0,
                i_opt_enable_hs=0,
                i_opt_ignore_vbus=0,
                o_stat_connected=stat_connected,
                o_stat_fs=stat_fs,
                o_stat_hs=stat_hs,
                o_stat_configured=stat_configured,

                i_buf_in_addr=self.usb2_control.buf_in_addr,
                i_buf_in_data=self.usb2_control.buf_in_data,
                i_buf_in_wren=self.usb2_control.buf_in_wren,
                o_buf_in_ready=self.usb2_control.buf_in_ready,
                i_buf_in_commit=self.usb2_control.buf_in_commit,
                i_buf_in_commit_len=self.usb2_control.buf_in_commit_len,
                o_buf_in_commit_ack=self.usb2_control.buf_in_commit_ack,

                i_buf_out_addr=self.usb2_control.buf_out_addr,
                o_buf_out_q=self.usb2_control.buf_out_q,
                o_buf_out_len=self.usb2_control.buf_out_len,
                o_buf_out_hasdata=self.usb2_control.buf_out_hasdata,
                i_buf_out_arm=self.usb2_control.buf_out_arm,
                o_buf_out_arm_ack=self.usb2_control.buf_out_arm_ack,

                o_vend_req_act=vend_req_act,
                o_vend_req_request=vend_req_request,
                o_vend_req_val=vend_req_val,

                o_err_crc_pid=err_crc_pid,
                o_err_crc_tok=err_crc_tok,
                o_err_crc_pkt=err_crc_pkt,
                o_err_pid_out_of_seq=err_pid_out_of_seq,
                o_err_setup_pkt=err_setup_pkt,

                o_dbg_frame_num=dbg_frame_num,
                o_dbg_linestate=dbg_linestate
            )
            platform.add_verilog_include_path(os.path.join("core"))
            platform.add_verilog_include_path(os.path.join("core", "usb2"))
            platform.add_source_dir(os.path.join("core", "usb2"))


            # usb2 debug
            if with_usb2_analyzer:
                analyzer_signals = [
                    dbg_frame_num,
                    dbg_linestate,

                    stat_connected,
                    stat_fs,
                    stat_hs,
                    stat_configured,

                    vend_req_act,
                    vend_req_request,
                    vend_req_val,

                    err_crc_pid,
                    err_crc_tok,
                    err_crc_pkt,
                    err_pid_out_of_seq,
                    err_setup_pkt
                ]
                self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 2048, cd="ulpi")


        # usb3 core
        if with_usb3:
            class USB3Control(Module, AutoCSR):
                def __init__(self):
                    self._phy_enable = CSRStorage()
                    self._core_enable = CSRStorage()

                    # probably not working but prevent synthesis optimizations
                    self._buf_in_addr = CSRStorage(9)
                    self._buf_in_data = CSRStorage(32)
                    self._buf_in_wren = CSR()
                    self._buf_in_request = CSRStatus()
                    self._buf_in_ready = CSRStatus()
                    self._buf_in_commit = CSR()
                    self._buf_in_commit_len = CSRStorage(11)
                    self._buf_in_commit_ack = CSRStatus()

                    self._buf_out_addr = CSRStorage(9)
                    self._buf_out_q = CSRStatus(32)
                    self._buf_out_len = CSRStatus(11)
                    self._buf_out_hasdata = CSRStatus()
                    self._buf_out_arm = CSR()
                    self._buf_out_arm_ack = CSRStatus()

                    # # #

                    self.phy_enable = self._phy_enable.storage
                    self.core_enable = self._core_enable.storage

                    self.buf_in_addr = self._buf_in_addr.storage
                    self.buf_in_data = self._buf_in_data.storage
                    self.buf_in_wren = self._buf_in_wren.re & self._buf_in_wren.r
                    self.buf_in_request = self._buf_in_request.status
                    self.buf_in_ready = self._buf_in_ready.status
                    self.buf_in_commit = self._buf_in_commit.re & self._buf_in_commit.r
                    self.buf_in_commit_len = self._buf_in_commit_len.storage
                    self.buf_in_commit_ack = self._buf_in_commit_ack.status

                    self.buf_out_addr = self._buf_out_addr.storage
                    self.buf_out_q = self._buf_out_q.status
                    self.buf_out_len = self._buf_out_len.status
                    self.buf_out_hasdata = self._buf_out_hasdata.status
                    self.buf_out_arm = self._buf_out_arm.re & self._buf_out_arm.r
                    self.buf_out_arm_ack = self._buf_out_arm_ack.status


            self.submodules.usb3_control = USB3Control()

            phy_pipe_pll_locked = Signal()
            phy_pipe_pll_fb = Signal()

            phy_pipe_half_clk_pll = Signal()
            phy_pipe_half_clk_phase_pll = Signal()
            phy_pipe_quarter_clk_pll = Signal()
            phy_pipe_tx_clk_phase_pll = Signal()

            phy_pipe_half_clk = Signal()
            phy_pipe_half_clk_phase = Signal()
            phy_pipe_quarter_clk = Signal()
            phy_pipe_tx_clk_phase = Signal()

            self.specials += [
                Instance("PLLE2_BASE",
                    p_STARTUP_WAIT="FALSE", o_LOCKED=phy_pipe_pll_locked,

                    # VCO @ 1GHz
                    p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=4.0,
                    p_CLKFBOUT_MULT=4, p_DIVCLK_DIVIDE=1,
                    i_CLKIN1=usb_pipe_data.rx_clk, i_CLKFBIN=phy_pipe_pll_fb,
                    o_CLKFBOUT=phy_pipe_pll_fb,

                    # 125MHz: 1/2 PCLK
                    p_CLKOUT0_DIVIDE=8, p_CLKOUT0_PHASE=0.0,
                    o_CLKOUT0=phy_pipe_half_clk_pll,

                    # 125MHz: 1/2 PCLK, phase shift 90
                    p_CLKOUT1_DIVIDE=8, p_CLKOUT1_PHASE=90.0,
                    o_CLKOUT1=phy_pipe_half_clk_phase_pll,

                    # 62.5MHz: 1/4 PCLK
                    p_CLKOUT2_DIVIDE=16, p_CLKOUT2_PHASE=0.0,
                    o_CLKOUT2=phy_pipe_quarter_clk_pll,

                    # 250Mhz: TX CLK, phase shift 90
                    p_CLKOUT3_DIVIDE=4, p_CLKOUT3_PHASE=90.0,
                    o_CLKOUT3=phy_pipe_tx_clk_phase_pll
                ),
                Instance("BUFG", i_I=phy_pipe_half_clk_pll, o_O=phy_pipe_half_clk),
                Instance("BUFG", i_I=phy_pipe_half_clk_phase_pll, o_O=phy_pipe_half_clk_phase),
                Instance("BUFG", i_I=phy_pipe_quarter_clk_pll, o_O=phy_pipe_quarter_clk),
                Instance("BUFG", i_I=phy_pipe_tx_clk_phase_pll, o_O=phy_pipe_tx_clk_phase),
            ]

            self.clock_domains.cd_phy_pipe_half = ClockDomain()
            self.clock_domains.cd_phy_pipe_half_phase = ClockDomain()
            self.clock_domains.cd_phy_pipe_quarter = ClockDomain()
            self.clock_domains.cd_phy_pipe_tx_phase = ClockDomain()
            self.comb += [
                self.cd_phy_pipe_half.clk.eq(phy_pipe_half_clk),
                self.cd_phy_pipe_half_phase.clk.eq(phy_pipe_half_clk_phase),
                self.cd_phy_pipe_quarter.clk.eq(phy_pipe_quarter_clk),
                self.cd_phy_pipe_tx_phase.clk.eq(phy_pipe_tx_clk_phase)
            ]
            self.specials += [
                AsyncResetSynchronizer(self.cd_phy_pipe_half, ~phy_pipe_pll_locked),
                AsyncResetSynchronizer(self.cd_phy_pipe_half_phase, ~phy_pipe_pll_locked),
                AsyncResetSynchronizer(self.cd_phy_pipe_quarter, ~phy_pipe_pll_locked),
                AsyncResetSynchronizer(self.cd_phy_pipe_tx_phase, ~phy_pipe_pll_locked)
            ]
            self.cd_phy_pipe_half.clk.attr.add("keep")
            self.cd_phy_pipe_half_phase.clk.attr.add("keep")
            self.cd_phy_pipe_quarter.clk.attr.add("keep")
            self.cd_phy_pipe_tx_phase.clk.attr.add("keep")
            self.platform.add_period_constraint(self.cd_phy_pipe_half.clk, 8.0)
            self.platform.add_period_constraint(self.cd_phy_pipe_half_phase.clk, 8.0)
            self.platform.add_period_constraint(self.cd_phy_pipe_quarter.clk, 16.0)
            self.platform.add_period_constraint(self.cd_phy_pipe_tx_phase.clk, 4.0)
            self.platform.add_false_path_constraints(
                self.crg.cd_sys.clk,
                self.cd_phy_pipe_half.clk,
                self.cd_phy_pipe_half_phase.clk,
                self.cd_phy_pipe_quarter.clk,
                self.cd_phy_pipe_tx_phase.clk)


            phy_pipe_rx_data = Signal(32)
            phy_pipe_rx_datak = Signal(4)
            phy_pipe_rx_valid = Signal(2)

            phy_pipe_tx_data = Signal(32)
            phy_pipe_tx_datak = Signal(4)

            phy_rx_status = Signal(6)
            phy_phy_status = Signal(2)

            dbg_pipe_state = Signal(6)
            dbg_ltssm_state = Signal(5)

            usb_pipe_status_phy_status = Signal()
            self.specials += Tristate(usb_pipe_status.phy_status, 0, ~usb3_reset_n, usb_pipe_status_phy_status)

            self.comb += usb3_reset_n.eq(self.usb3_control.phy_enable)
            self.specials += Instance("usb3_top",
                i_ext_clk=ClockSignal(),
                i_reset_n=self.usb3_control.core_enable,

                i_phy_pipe_half_clk=ClockSignal("phy_pipe_half"),
                i_phy_pipe_half_clk_phase=ClockSignal("phy_pipe_half_phase"),
                i_phy_pipe_quarter_clk=ClockSignal("phy_pipe_quarter"),

                i_phy_pipe_rx_data=phy_pipe_rx_data,
                i_phy_pipe_rx_datak=phy_pipe_rx_datak,
                i_phy_pipe_rx_valid=phy_pipe_rx_valid,
                o_phy_pipe_tx_data=phy_pipe_tx_data,
                o_phy_pipe_tx_datak=phy_pipe_tx_datak,

                #o_phy_reset_n=,
                #o_phy_out_enable=,
                o_phy_phy_reset_n=usb_pipe_ctrl.phy_reset_n,
                o_phy_tx_detrx_lpbk=usb_pipe_ctrl.tx_detrx_lpbk,
                o_phy_tx_elecidle=usb_pipe_ctrl.tx_elecidle,
                io_phy_rx_elecidle=usb_pipe_status.rx_elecidle,
                i_phy_rx_status=phy_rx_status,
                o_phy_power_down=usb_pipe_ctrl.power_down,
                i_phy_phy_status_i=phy_phy_status,
                #o_phy_phy_status_o=,
                i_phy_pwrpresent=usb_pipe_status.pwr_present,

                o_phy_tx_oneszeros=usb_pipe_ctrl.tx_oneszeros,
                o_phy_tx_deemph=usb_pipe_ctrl.tx_deemph,
                o_phy_tx_margin=usb_pipe_ctrl.tx_margin,
                o_phy_tx_swing=usb_pipe_ctrl.tx_swing,
                o_phy_rx_polarity=usb_pipe_ctrl.rx_polarity,
                o_phy_rx_termination=usb_pipe_ctrl.rx_termination,
                o_phy_rate=usb_pipe_ctrl.rate,
                o_phy_elas_buf_mode=usb_pipe_ctrl.elas_buf_mode,

                i_buf_in_addr=self.usb3_control.buf_in_addr,
                i_buf_in_data=self.usb3_control.buf_in_data,
                i_buf_in_wren=self.usb3_control.buf_in_wren,
                o_buf_in_request=self.usb3_control.buf_in_request,
                o_buf_in_ready=self.usb3_control.buf_in_ready,
                i_buf_in_commit=self.usb3_control.buf_in_commit,
                i_buf_in_commit_len=self.usb3_control.buf_in_commit_len,
                o_buf_in_commit_ack=self.usb3_control.buf_in_commit_ack,

                i_buf_out_addr=self.usb3_control.buf_out_addr,
                o_buf_out_q=self.usb3_control.buf_out_q,
                o_buf_out_len=self.usb3_control.buf_out_len,
                o_buf_out_hasdata=self.usb3_control.buf_out_hasdata,
                i_buf_out_arm=self.usb3_control.buf_out_arm,
                o_buf_out_arm_ack=self.usb3_control.buf_out_arm_ack,

                #o_vend_req_act=,
                #o_vend_req_request=,
                #o_vend_req_val=,

                o_dbg_pipe_state=dbg_pipe_state,
                o_dbg_ltssm_state=dbg_ltssm_state
            )
            platform.add_verilog_include_path(os.path.join("core"))
            platform.add_verilog_include_path(os.path.join("core", "usb3"))
            platform.add_source_dir(os.path.join("core", "usb3"))

            # ddr inputs
            self.specials += Instance("IDDR",
                p_DDR_CLK_EDGE="SAME_EDGE_PIPELINED",
                i_C=ClockSignal("phy_pipe_half"), i_CE=1, i_S=0, i_R=0,
                i_D=usb_pipe_data.rx_valid, o_Q1=phy_pipe_rx_valid[0], o_Q2=phy_pipe_rx_valid[1],
            )
            for i in range(16):
                self.specials += Instance("IDDR",
                    p_DDR_CLK_EDGE="SAME_EDGE_PIPELINED",
                    i_C=ClockSignal("phy_pipe_half"), i_CE=1, i_S=0, i_R=0,
                    i_D=usb_pipe_data.rx_data[i], o_Q1=phy_pipe_rx_data[i], o_Q2=phy_pipe_rx_data[16+i],
                )
            for i in range(2):
                self.specials += Instance("IDDR",
                    p_DDR_CLK_EDGE="SAME_EDGE_PIPELINED",
                    i_C=ClockSignal("phy_pipe_half"), i_CE=1, i_S=0, i_R=0,
                    i_D=usb_pipe_data.rx_datak[i], o_Q1=phy_pipe_rx_datak[i], o_Q2=phy_pipe_rx_datak[2+i],
                )
            for i in range(3):
                self.specials += Instance("IDDR",
                    p_DDR_CLK_EDGE="SAME_EDGE_PIPELINED",
                    i_C=ClockSignal("phy_pipe_half"), i_CE=1, i_S=0, i_R=0,
                    i_D=usb_pipe_status.rx_status[i], o_Q1=phy_rx_status[i], o_Q2=phy_rx_status[3+i],
                )
            self.specials += Instance("IDDR",
                p_DDR_CLK_EDGE="SAME_EDGE_PIPELINED",
                i_C=ClockSignal("phy_pipe_half"), i_CE=1, i_S=0, i_R=0,
                i_D=usb_pipe_status_phy_status, o_Q1=phy_phy_status[0], o_Q2=phy_phy_status[1],
            )

            # ddr outputs
            self.specials += Instance("ODDR",
                p_DDR_CLK_EDGE="SAME_EDGE",
                i_C=ClockSignal("phy_pipe_tx_phase"), i_CE=1, i_S=0, i_R=0,
                i_D1=1, i_D2=0, o_Q=usb_pipe_data.tx_clk,
            )
            for i in range(16):
                self.specials += Instance("ODDR",
                    p_DDR_CLK_EDGE="SAME_EDGE",
                    i_C=ClockSignal("phy_pipe_half_phase"), i_CE=1, i_S=0, i_R=0,
                    i_D1=phy_pipe_tx_data[i], i_D2=phy_pipe_tx_data[16+i], o_Q=usb_pipe_data.tx_data[i],
                )
            for i in range(2):
                self.specials += Instance("ODDR",
                    p_DDR_CLK_EDGE="SAME_EDGE",
                    i_C=ClockSignal("phy_pipe_half_phase"), i_CE=1, i_S=0, i_R=0,
                    i_D1=phy_pipe_tx_datak[i], i_D2=phy_pipe_tx_datak[2+i], o_Q=usb_pipe_data.tx_datak[i],
                )

            # usb3 debug
            if with_usb3_analyzer:
                analyzer_signals = [
                    dbg_pipe_state,
                    dbg_ltssm_state,

                    usb_pipe_ctrl.tx_detrx_lpbk,
                    usb_pipe_ctrl.tx_elecidle,
                    usb_pipe_status.rx_elecidle,
                    usb_pipe_ctrl.power_down,
                    usb_pipe_status.phy_status,
                    usb_pipe_status.pwr_present,

                    usb_pipe_ctrl.tx_oneszeros,
                    usb_pipe_ctrl.tx_deemph,
                    usb_pipe_ctrl.tx_margin,
                    usb_pipe_ctrl.tx_swing,
                    usb_pipe_ctrl.rx_polarity,
                    usb_pipe_ctrl.rx_termination,
                    usb_pipe_ctrl.rate,
                    usb_pipe_ctrl.elas_buf_mode,

                    phy_pipe_rx_valid,
                    phy_pipe_rx_data,
                    phy_pipe_rx_datak,

                    phy_pipe_tx_data,
                    phy_pipe_tx_datak
                ]
                self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 2048, cd="phy_pipe_half")

    def do_exit(self, vns):
        if hasattr(self, "analyzer"):
            self.analyzer.export_csv(vns, "test/analyzer.csv")


def main():
    platform = Platform(toolchain="vivado")
    soc = USBSoC(platform)
    builder = Builder(soc, output_dir="build", csr_csv="test/csr.csv")
    vns = builder.build()
    soc.do_exit(vns)


if __name__ == "__main__":
    main()
