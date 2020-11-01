-- SPDX-License-Identifier: BSD-2-Clause
-- SPDX-FileCopyrightText: Copyright (c) 2020 Marian Sauer

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use std.textio.all;

entity usb2_descrip_rom is
  port (
    adr : in std_logic_vector(7 downto 0);
    clk : in std_logic;
    dat_r : out std_logic_vector(7 downto 0)
  );
end entity;



architecture rtl of usb2_descrip_rom is
  type ramType is array (0 to 255) of std_logic_vector(7 downto 0);

  function char_to_binary(v : character) return std_logic_vector is
    variable hex_val : std_logic_vector(3 downto 0);
  begin
    if(v >= '0' and v <= '9') then
      hex_val := std_logic_vector(to_unsigned(character'pos(v) - character'pos('0'), 4));
    elsif (v >= 'a' and v <= 'f') then
      hex_val := std_logic_vector(to_unsigned(character'pos(v) - character'pos('a') + 10, 4));
    elsif (v >= 'A' and v <= 'F') then
      hex_val := std_logic_vector(to_unsigned(character'pos(v) - character'pos('A') + 10, 4));
    else
      hex_val := "XXXX";
      assert false report "Invalid hex character '" & v & "'";
    end if;
    return hex_val;
  end function;

  function rom_init(filename : string) return ramType is
    variable temp : ramType;
    file file_ptr : text;
    variable text_line : line;
    variable high_nibbel : character;
    variable low_nibbel : character;
  begin
    file_open(file_ptr, filename, READ_MODE);
    for i in 0 to ramType'high loop
      readline (file_ptr, text_line);
      read (text_line, high_nibbel);
      read (text_line, low_nibbel);
      temp(i) := char_to_binary(high_nibbel) & char_to_binary(low_nibbel);
    end loop;
    file_close(file_ptr);
    return temp;
  end function;


  signal memory : ramType := rom_init("usb2_descrip_rom.init");
  signal adr_reg : std_logic_vector(7 downto 0);
begin

  process (clk) is
  begin
    if rising_edge(clk) then
      adr_reg <= adr;
    end if;
  end process;

  dat_r <= memory(to_integer(unsigned(adr_reg)));
end architecture;
