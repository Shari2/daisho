-- SPDX-License-Identifier: BSD-2-Clause
-- SPDX-FileCopyrightText: Copyright (c) 2020 Marian Sauer


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- oddr clock forward
library unisim;
use unisim.vcomponents.all;

entity top is
port
(
  i_clk_100M : in std_logic;
  i_reset_n : in std_logic;
  io_ulpi_data : inout std_logic_vector(7 downto 0);
  i_ulpi_dir : in std_logic;
  i_ulpi_nxt : in std_logic;
  o_ulpi_clk_60M : out std_logic;
  o_ulpi_reset_n : out std_logic;
  o_ulpi_stp : out std_logic;
  o_sdcard_cs : out std_logic;
  o_sdcard_di : out std_logic;
  o_sdcard_do : out std_logic;
  o_sdcard_nc : out std_logic;
  o_sdcard_rsv : out std_logic;
  o_sdcard_sck : out std_logic
);
end top;

architecture rtl of top is

component usb2_top
port (
  buf_in_addr : in std_logic_vector(8 downto 0);
  buf_in_commit : in std_logic;
  buf_in_commit_ack : out std_logic;
  buf_in_commit_len : in std_logic_vector(9 downto 0);
  buf_in_data : in std_logic_vector(7 downto 0);
  buf_in_ready : out std_logic;
  buf_in_wren : in std_logic;
  buf_out_addr : in std_logic_vector(8 downto 0);
  buf_out_arm : in std_logic;
  buf_out_arm_ack : out std_logic;
  buf_out_hasdata : out std_logic;
  buf_out_len : out std_logic_vector(9 downto 0);
  buf_out_q : out std_logic_vector(7 downto 0);
  dbg_frame_num : out std_logic_vector(10 downto 0);
  dbg_linestate : out std_logic_vector(1 downto 0);
  err_crc_pid : out std_logic;
  err_crc_pkt : out std_logic;
  err_crc_tok : out std_logic;
  err_pid_out_of_seq : out std_logic;
  err_setup_pkt : out std_logic;
  ext_clk : in std_logic;
  opt_disable_all : in std_logic;
  opt_enable_hs : in std_logic;
  opt_ignore_vbus : in std_logic;
  phy_ulpi_clk : in std_logic;
  phy_ulpi_d : inout std_logic_vector(7 downto 0);
  phy_ulpi_dir : in std_logic;
  phy_ulpi_nxt : in std_logic;
  phy_ulpi_stp : out std_logic;
  reset_n : in std_logic;
  reset_n_out : out std_logic;
  stat_configured : out std_logic;
  stat_connected : out std_logic;
  stat_fs : out std_logic;
  stat_hs : out std_logic;
  vend_req_act : out std_logic;
  vend_req_request : out std_logic_vector(7 downto 0);
  vend_req_val : out std_logic_vector(15 downto 0)
);
end component;

  signal buf_in_addr : std_logic_vector(8 downto 0);
  signal buf_in_commit : std_logic;
  signal buf_in_commit_ack : std_logic;
  signal buf_in_commit_len : std_logic_vector(9 downto 0);
  signal buf_in_data : std_logic_vector(7 downto 0);
  signal buf_in_ready : std_logic;
  signal buf_in_wren : std_logic;
  signal buf_out_addr : std_logic_vector(8 downto 0);
  signal buf_out_arm : std_logic;
  signal buf_out_arm_ack : std_logic;
  signal buf_out_hasdata : std_logic;
  signal buf_out_len : std_logic_vector(9 downto 0);
  signal buf_out_q : std_logic_vector(7 downto 0);
  signal dbg_frame_num : std_logic_vector(10 downto 0);
  signal dbg_linestate : std_logic_vector(1 downto 0);
  signal err_crc_pid : std_logic;
  signal err_crc_pkt : std_logic;
  signal err_crc_tok : std_logic;
  signal err_pid_out_of_seq : std_logic;
  signal err_setup_pkt : std_logic;
  signal opt_disable_all : std_logic;
  signal opt_enable_hs : std_logic;
  signal opt_ignore_vbus : std_logic;
  signal stat_configured : std_logic;
  signal stat_connected : std_logic;
  signal stat_fs : std_logic;
  signal stat_hs : std_logic;
  signal vend_req_act : std_logic;
  signal vend_req_request : std_logic_vector(7 downto 0);
  signal vend_req_val : std_logic_vector(15 downto 0);

  signal async_assert_sync_deassert_reset_n : std_logic_vector(1 downto 0);

  signal debug : std_logic_vector(5 downto 0);

  signal ulpi_reset_n : std_logic;
  signal pll_locked : std_logic;

  signal ulpi_clk_60M : std_logic;

  signal clk_100M : std_logic;
  signal clk_100M_reset_n : std_logic;
  signal debug_clk_forward : std_logic;

  signal async_reset_n : std_logic;

begin

  -- rename signals for easier mapping
  o_sdcard_rsv <= debug(0); -- SD_DAT1
  o_sdcard_do  <= debug(1); -- SD_DAT0
  o_sdcard_sck <= debug(2); -- SD_CLK
  o_sdcard_di  <= debug(3); -- SD_CMD
  o_sdcard_cs  <= debug(4); -- SD_DAT3
  o_sdcard_nc  <= debug(5); -- SD_DAT2

  debug <= b"00" & i_ulpi_dir & debug_clk_forward & async_reset_n & ulpi_reset_n;
  o_ulpi_reset_n <= ulpi_reset_n;

  buf_in_addr <= (others => '0');
  buf_in_commit <= '0';
  buf_in_commit_len <= (others => '0');
  buf_in_data <= (others => '0');
  buf_in_wren <= '0';
  buf_out_addr <= (others => '0');
  buf_out_arm <= '0';
  opt_disable_all <= '0';
  opt_enable_hs <= '0';
  opt_ignore_vbus <= '0';
  clk_100M_reset_n <= async_assert_sync_deassert_reset_n(1);

  sys_pll_inst : entity work.sys_pll
  port map
  (
    i_clk_100M => i_clk_100M,
    o_clk_100M => clk_100M,
    o_clk_60M => ulpi_clk_60M,
    i_async_reset => not i_reset_n,
    o_locked => pll_locked
  );


  -- ULPI Clock Input Mode
  -- Phy datasheet "When using ULPI Clock Input Mode, the Link must supply the 60 MHz ULPI clock to the USB3340. In this mode the 60 MHz ULPI Clock is connected to the REFCLK pin, and the CLKOUT pin is tied high to VDDIO."
  -- ULPI specificatoin "The Link ... should not activate its clock output until its PLL is stable. An unstable Link clock may cause the PHY PLL to take longer to stabilize."

  ulpi_clock_forward_inst : oddr2
  generic map
  (
    DDR_ALIGNMENT => "C0",
    SRTYPE => "ASYNC"
  )
  port map
  (
    q => o_ulpi_clk_60M,
    c0 => ulpi_clk_60M,
    c1 => not(ulpi_clk_60M),
    d0 => '1',
    d1 => '0',
    r => not pll_locked
  );

  -- Phy datasheet "The REFCLK should be enabled when the RESETB pin is brought high"
  ulpi_reset_n <= pll_locked;



  debug_clock_forward_inst : oddr2
  generic map
  (
    DDR_ALIGNMENT => "C0",
    SRTYPE => "ASYNC"
  )
  port map
  (
    q => debug_clk_forward,
    c0 => ulpi_clk_60M,
    c1 => not(ulpi_clk_60M),
    d0 => '1',
    d1 => '0'
  );

  async_reset_n <= i_reset_n and pll_locked;

  process(clk_100M, async_reset_n)
  begin
    if async_reset_n = '0' then
      async_assert_sync_deassert_reset_n <= (others => '0');
    elsif rising_edge(clk_100M) then
      async_assert_sync_deassert_reset_n <= async_assert_sync_deassert_reset_n(0) & '1';
    end if;
  end process;


  u : usb2_top
  port map
  (
    buf_in_addr        => buf_in_addr       ,
    buf_in_commit      => buf_in_commit     ,
    buf_in_commit_ack  => buf_in_commit_ack ,
    buf_in_commit_len  => buf_in_commit_len ,
    buf_in_data        => buf_in_data       ,
    buf_in_ready       => buf_in_ready      ,
    buf_in_wren        => buf_in_wren       ,
    buf_out_addr       => buf_out_addr      ,
    buf_out_arm        => buf_out_arm       ,
    buf_out_arm_ack    => buf_out_arm_ack   ,
    buf_out_hasdata    => buf_out_hasdata   ,
    buf_out_len        => buf_out_len       ,
    buf_out_q          => buf_out_q         ,
    dbg_frame_num      => dbg_frame_num     ,
    dbg_linestate      => dbg_linestate     ,
    err_crc_pid        => err_crc_pid       ,
    err_crc_pkt        => err_crc_pkt       ,
    err_crc_tok        => err_crc_tok       ,
    err_pid_out_of_seq => err_pid_out_of_seq,
    err_setup_pkt      => err_setup_pkt     ,
    ext_clk            => clk_100M,
    opt_disable_all    => opt_disable_all   ,
    opt_enable_hs      => opt_enable_hs     ,
    opt_ignore_vbus    => opt_ignore_vbus   ,
    phy_ulpi_clk       => ulpi_clk_60M,
    phy_ulpi_d         => io_ulpi_data,
    phy_ulpi_dir       => i_ulpi_dir,
    phy_ulpi_nxt       => i_ulpi_nxt,
    phy_ulpi_stp       => o_ulpi_stp,
    reset_n            => clk_100M_reset_n,
    reset_n_out        => open,
    stat_configured    => stat_configured   ,
    stat_connected     => stat_connected    ,
    stat_fs            => stat_fs           ,
    stat_hs            => stat_hs           ,
    vend_req_act       => vend_req_act      ,
    vend_req_request   => vend_req_request  ,
    vend_req_val       => vend_req_val
  );

end architecture rtl;

