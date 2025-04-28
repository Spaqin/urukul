[![QUARTIQ Matrix Chat](https://img.shields.io/matrix/quartiq:matrix.org)](https://matrix.to/#/#quartiq:matrix.org)

# Urukul CPLD code

[Urukul overview](https://github.com/sinara-hw/Urukul/wiki)

[Urukul Schematics/Layout](https://github.com/sinara-hw/Urukul/releases)

[NU-Servo](https://github.com/m-labs/nu-servo)

## Building (Xilinx)

Needs [migen](https://github.com/m-labs/migen) and [Xilinx ISE](https://www.xilinx.com/products/design-tools/ise-design-suite.html). Assumes ISE is installed in ``/opt/Xilinx``.

```
make
```

## Flashing (Xilinx)

With Digilent [JTAG HS2](https://store.digilentinc.com/jtag-hs2-programming-cable/) cable:

  - download firmware to dongle. Manually (adjust USB bus as needed):
  ```
  /sbin/fxload -t fx2 -I /opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/xusb_xp2.hex -D /dev/bus/usb/001/*`cat /sys/bus/usb/devices/1-3/devnum`
  ```
  or automatically via the ``udev`` rule:
  ```
  SUBSYSTEM=="usb", ACTION="add", ATTR{idVendor}=="0403", ATTR{idProduct}=="6014", ATTR{manufacturer}=="Digilent", RUN+="/usr/bin/fxload -v -t fx2 -I /opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/xusb_xp2.hex -D $tempnode"
  ```

  - install [xc3sprog](http://xc3sprog.sourceforge.net/)

  - ``flash_xc3.sh jtaghs2``

  - look for ``Verify: Success``

## Building (Urukul DIOT, ICE40)

Needs [migen](https://github.com/m-labs/migen), ``yosys``, ``nextpnr``, ``icestorm`` (available on Nix; todo: make a flake).

With all these you can just call the python script:

```
python urukul_ice.py
```

## Flashing (Urukul DIOT, ICE40)

Use [kasli-i2c](https://github.com/Spaqin/kasli-i2c/tree/flash_urukul) (may work after Urukul design is fixed).

Otherwise you can also use an FT232H-based board. Connect the wires as follows. Top left is closest to the CPLD, right is facing the edge. Bottom is towards the end of the edge.

```
D4    D1
D2    D0
GND   X
X     X
D7    D6
```

Use ``iceprog`` (available with ``icestorm`` package):

```
iceprog build/urukul.bin
```

On development boards you may need to toggle the CRESET pin with kasli-i2c, then use FT232H to flash.

# License

GPLv3+
