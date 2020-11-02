-- SPDX-License-Identifier: BSD-2-Clause
-- SPDX-FileCopyrightText: Copyright (c) 2020 Marian Sauer

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- IBUFG, DCM_SP, BUFG primitive
library unisim;
use unisim.vcomponents.all;

entity sys_pll is
port
(
  i_clk_100M    : in  std_logic;
  i_async_reset : in  std_logic;
  o_clk_100M    : out std_logic;
  o_clk_60M     : out std_logic;
  o_locked      : out std_logic
);
end sys_pll;

architecture rtl of sys_pll is
  signal clk_100M          : std_logic;
  signal clk_out1_internal : std_logic;
  signal clkfb             : std_logic;
  signal clk0              : std_logic;
  signal clkfx             : std_logic;
  signal clkfbout          : std_logic;
  signal locked_internal   : std_logic;
begin

  clkin1_ibuf_inst : IBUFG
  port map
  (
    O => clk_100M,
    I => i_clk_100M
  );

  dcm_sp_inst: DCM_SP
  generic map
  (
    CLKDV_DIVIDE       => 2.000,
    CLKFX_DIVIDE       => 5,
    CLKFX_MULTIPLY     => 3,
    CLKIN_DIVIDE_BY_2  => FALSE,
    CLKIN_PERIOD       => 10.0,
    CLKOUT_PHASE_SHIFT => "NONE",
    CLK_FEEDBACK       => "1X",
    DESKEW_ADJUST      => "SYSTEM_SYNCHRONOUS",
    PHASE_SHIFT        => 0,
    STARTUP_WAIT       => FALSE
  )
  port map
  (
    CLKIN    => clk_100M,
    CLKFB    => clkfb,
    CLK0     => clk0,
    CLK90    => open,
    CLK180   => open,
    CLK270   => open,
    CLK2X    => open,
    CLK2X180 => open,
    CLKFX    => clkfx,
    CLKFX180 => open,
    CLKDV    => open,
    PSCLK    => '0',
    PSEN     => '0',
    PSINCDEC => '0',
    PSDONE   => open,
    LOCKED   => locked_internal,
    STATUS   => open,
    RST      => i_async_reset,
    DSSEN    => '0'
  );

  o_locked <= locked_internal;

  clkfb <= clk_out1_internal;

  clkout1_buf : BUFG
  port map
  (
    O => clk_out1_internal,
    I => clk0
  );


  o_clk_100M <= clk_out1_internal;

  clkout2_buf : BUFG
  port map
  (
    O => o_clk_60M,
    I => clkfx
  );

end architecture rtl;
