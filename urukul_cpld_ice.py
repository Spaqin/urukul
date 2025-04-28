from migen.build.generic_platform import *
from migen.build.lattice import LatticePlatform

_io = [
    ("clk25", 0, Pins("K9"), IOStandard("LVCMOS33")),
    ("tp", 0, Pins("H14"), IOStandard("LVCMOS33")),
    ("tp", 1, Pins("J16"), IOStandard("LVCMOS33")),
    ("tp", 2, Pins("J15"), IOStandard("LVCMOS33")),
    ("tp", 3, Pins("K16"), IOStandard("LVCMOS33")),
    ("tp", 4, Pins("K15"), IOStandard("LVCMOS33")),
    ("ifc_mode", 0, Pins("E16 D16 D15 C16"), IOStandard("LVCMOS33")),
    # two more user switches marked SW2 on PCB
    ("sw", 0, Pins("F15 F16"), IOStandard("LVCMOS33")),
    ("hw_rev", 0, Pins("R3 T2 R2 T1"), IOStandard("LVCMOS33")),
    # 10k low: AD9912, 0R high: AD9910
    ("variant", 0, Pins("T3"), IOStandard("LVCMOS33")),
    ("err", 0, Pins("L7"), IOStandard("LVCMOS25")),
    (
        "clk",
        0,
        Subsignal("div", Pins("P6")),
        Subsignal("in_sel", Pins("P5")),
        Subsignal("mmcx_osc_sel", Pins("M8")),
        Subsignal("osc_en_n", Pins("T5")),
        IOStandard("LVCMOS33"),
    ),
    (
        "dds_common",
        0,
        Subsignal("master_reset", Pins("C7")),
        Subsignal("io_reset", Pins("E14")),
        IOStandard("LVCMOS33"),
    ),
    (
        "dds_sync",
        0,
        Subsignal("clk0", Pins("B4"), Misc("PULLUP")),  # DDS_SYNC_CLK0
        Subsignal("clk_out_en", Pins("N6")),  # DDS_SYNC_CLK_OUTEN
        Subsignal("sync_sel", Pins("N5")),  # DDS_SYNC_CLKSEL
        Subsignal("sync_out_en", Pins("N7")),  # DDS_SYNC_OUTEN
        IOStandard("LVCMOS33"),
    ),
    (
        "att",
        0,
        Subsignal("clk", Pins("B3")),
        Subsignal("rst_n", Pins("D8")),
        Subsignal("le", Pins("D13 C11 D4 A2")),
        Subsignal("s_in", Pins("C13 C12 C5 A1")),
        Subsignal("s_out", Pins("C14 E11 C4 F9")),
        IOStandard("LVCMOS33"),
    ),
    (
        "dds",
        0,
        Subsignal("rf_sw", Pins("A7")),
        Subsignal("led", Pins("G13 G14")),
        Subsignal("smp_err", Pins("F7"), Misc("PULLUP")),
        Subsignal("pll_lock", Pins("E5"), Misc("PULLUP")),
        Subsignal("io_update", Pins("B12")),
        Subsignal("profile", Pins("A15 B13 B14")),
        Subsignal("osk", Pins("A16")),
        Subsignal("drover", Pins("B15")),
        Subsignal("drhold", Pins("D14")),
        Subsignal("drctl", Pins("B16")),
        Subsignal("reset", Pins("B11")),
        Subsignal("sck", Pins("B8")),
        Subsignal("sdo", Pins("A11"), Misc("PULLUP")),
        Subsignal("sdi", Pins("A10")),
        Subsignal("cs_n", Pins("B10")),
        IOStandard("LVCMOS33"),
    ),
    (
        "dds",
        1,
        Subsignal("rf_sw", Pins("A6")),
        Subsignal("led", Pins("F14 F13")),
        Subsignal("smp_err", Pins("D11"), Misc("PULLUP")),
        Subsignal("pll_lock", Pins("C10"), Misc("PULLUP")),
        Subsignal("io_update", Pins("L16")),
        Subsignal("profile", Pins("J14 K14 J10")),
        Subsignal("osk", Pins("H12")),
        Subsignal("drover", Pins("G15")),
        Subsignal("drhold", Pins("B9")),
        Subsignal("drctl", Pins("G16")),
        Subsignal("reset", Pins("A9")),
        Subsignal("sck", Pins("G11")),
        Subsignal("sdo", Pins("N16"), Misc("PULLUP")),
        Subsignal("sdi", Pins("M16")),
        Subsignal("cs_n", Pins("M15")),
        IOStandard("LVCMOS33"),
    ),
    (
        "dds",
        2,
        Subsignal("rf_sw", Pins("C8")),
        Subsignal("led", Pins("E13 G12")),
        Subsignal("smp_err", Pins("B5"), Misc("PULLUP")),
        Subsignal("pll_lock", Pins("P4"), Misc("PULLUP")),
        Subsignal("io_update", Pins("C6")),
        Subsignal("profile", Pins("E9 E6 D7")),
        Subsignal("osk", Pins("E10")),
        Subsignal("drover", Pins("D9")),
        Subsignal("drhold", Pins("D10")),
        Subsignal("drctl", Pins("C9")),
        Subsignal("reset", Pins("B7")),
        Subsignal("sck", Pins("C3")),
        Subsignal("sdo", Pins("D5"), Misc("PULLUP")),
        Subsignal("sdi", Pins("A5")),
        Subsignal("cs_n", Pins("D6")),
        IOStandard("LVCMOS33"),
    ),
    (
        "dds",
        3,
        Subsignal("rf_sw", Pins("B6")),
        Subsignal("led", Pins("H13 F11")),
        Subsignal("smp_err", Pins("P15"), Misc("PULLUP")),
        Subsignal("pll_lock", Pins("P16"), Misc("PULLUP")),
        Subsignal("io_update", Pins("M14")),
        Subsignal("profile", Pins("L12 M13 R14")),
        Subsignal("osk", Pins("J12")),
        Subsignal("drover", Pins("J11")),
        Subsignal("drhold", Pins("G10")),
        Subsignal("drctl", Pins("H11")),
        Subsignal("reset", Pins("J13")),
        Subsignal("sck", Pins("K13")),
        Subsignal("sdo", Pins("L13"), Misc("PULLUP")),
        Subsignal("sdi", Pins("L14")),
        Subsignal("cs_n", Pins("R15")),
        IOStandard("LVCMOS33"),
    ),
    # yosys/nextpnr get confused if these are not broken up
    # EEM 0
    ("eem", 0, Subsignal("n", Pins("J5")), Subsignal("p", Pins("G1"))),  # SCLK
    ("eem", 1, Subsignal("n", Pins("K4")), Subsignal("p", Pins("M1"))),  # MOSI
    ("eem", 2, Subsignal("n", Pins("K1")), Subsignal("p", Pins("K3"))),  # MISO/NU_CLK
    ("eem", 3, Subsignal("n", Pins("J4")), Subsignal("p", Pins("H2"))),  # CS0
    ("eem", 4, Subsignal("n", Pins("H4")), Subsignal("p", Pins("G2"))),  # CS1
    ("eem", 5, Subsignal("n", Pins("G4")), Subsignal("p", Pins("E3"))),  # CS2/NU_CS
    ("eem", 6, Subsignal("n", Pins("F4")), Subsignal("p", Pins("D2"))),  # IO_UPDATE
    ("eem", 7, Subsignal("n", Pins("E4")), Subsignal("p", Pins("B2"))),  # DDS_RESET/SYNC_DAT
    # EEM 1
    ("eem", 8, Subsignal("n", Pins("J3")), Subsignal("p", Pins("H1"))),  # SYNC_CLK/NU_MOSI0
    ("eem", 9, Subsignal("n", Pins("L4")), Subsignal("p", Pins("L1"))),  # SYNC_IN/NU_MOSI1
    ("eem", 10, Subsignal("n", Pins("J2")), Subsignal("p", Pins("J1"))), # IO_UPDATE_RET/NU_MOSI2
    ("eem", 11, Subsignal("n", Pins("H3")), Subsignal("p", Pins("F2"))), # NU_MOSI3
    ("eem", 12, Subsignal("n", Pins("H5")), Subsignal("p", Pins("E2"))), # SW0
    ("eem", 13, Subsignal("n", Pins("G5")), Subsignal("p", Pins("D1"))), # SW1
    ("eem", 14, Subsignal("n", Pins("C1")), Subsignal("p", Pins("C2"))), # SW2
    ("eem", 15, Subsignal("n", Pins("F5")), Subsignal("p", Pins("B1"))), # SW3
]


class Platform(LatticePlatform):
    default_clk_name = "clk25"
    default_clk_period = 40.0

    def __init__(self):
        LatticePlatform.__init__(self, "ice40-hx8k-ct256", _io, toolchain="icestorm")
