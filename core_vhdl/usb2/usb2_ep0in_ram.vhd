-- SPDX-License-Identifier: BSD-2-Clause
-- SPDX-FileCopyrightText: Copyright (c) 2020 Marian Sauer

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity usb2_ep0in_ram is
  generic
  (
    DATA_WIDTH : positive := 8;
    ADDRESS_WIDTH : positive := 6
  );
  port (
    clk : in std_logic;
    rd_adr : in std_logic_vector(ADDRESS_WIDTH - 1  downto 0);
    rd_dat_r : out std_logic_vector(DATA_WIDTH - 1 downto 0);
    wr_adr : in std_logic_vector(ADDRESS_WIDTH - 1 downto 0);
    wr_dat_w : in std_logic_vector(DATA_WIDTH - 1 downto 0);
    wr_we : in std_logic
  );
end entity;


architecture rtl of usb2_ep0in_ram is
  type ramType is array (2**ADDRESS_WIDTH - 1 downto 0) of std_logic_vector(DATA_WIDTH -1 downto 0);
  signal memory : ramType;

  signal read_data_register : std_logic_vector(DATA_WIDTH -1  downto 0);
  signal read_address_register : std_logic_vector(ADDRESS_WIDTH - 1 downto 0);
begin
  rd_dat_r <= read_data_register;

  process (clk) is
  begin
    if rising_edge(clk) then
      if wr_we = '1' then
        memory(to_integer(unsigned(wr_adr))) <= wr_dat_w;
      end if;
    end if;
  end process;

  process (clk) is
  begin
    if rising_edge(clk) then
      read_address_register <= rd_adr;
    end if;
  end process;

  process (clk) is
  begin
    if rising_edge(clk) then
      read_data_register <= memory(to_integer(unsigned(read_address_register)));
    end if;
  end process;
end architecture;
