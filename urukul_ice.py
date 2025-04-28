from migen import *


# increment this if the behavior (LEDs, registers, EEM pins) changes
__proto_rev__ = 8


class SR(Module):
    """
    Shift register, SPI slave

    * CPOL = 0 (clock idle low during ~SEL)
    * CPHA = 0 (sample on first edge, shift on second)
    * SPI mode 0
    * samples SDI on rising clock edges (SCK1 domain)
    * shifts out SDO on falling clock edges (SCK0 domain)
    * MSB first
    * the first output bit (MSB) is undefined
    * the first output bit is available from the start of the SEL cycle until
      the first falling edge
    * the first input bit is sampled on the first rising edge
    * on the first rising edge with SEL assered, the parallel data DO
      is loaded into the shift register
    * following at least one rising clock edge, on the deassertion of SEL,
      the shift register is loaded into the parallel data register DI
    """

    def __init__(self, width):
        self.sdi = Signal()
        self.sdo = Signal()
        self.sel = Signal()

        self.di = Signal(width)
        self.do = Signal(width)

        # # #

        sr = Signal(width)

        self.clock_domains.cd_le = ClockDomain("le", reset_less=True)
        # clock the latch domain from selection deassertion but only after
        # there was a serial clock edge with asserted select (i.e. ignore
        # glitches).
        self.specials += Instance("SB_DFFES", i_D=0, i_C=ClockSignal("sck1"),
                                  i_E=self.sel, i_S=~self.sel, o_Q=self.cd_le.clk)
        self.sync.sck0 += [
                If(self.sel,
                    self.sdo.eq(sr[-1]),
                )
        ]
        self.sync.sck1 += [
                If(self.sel,
                    sr[0].eq(self.sdi),
                    If(self.cd_le.clk,
                        sr[1:].eq(self.do[:-1])
                    ).Else(
                        sr[1:].eq(sr[:-1])
                    )
                )
        ]
        self.sync.le += [
                self.di.eq(sr)
        ]


class CFG(Module):
    """Configuration register

    The configuration register is updated from the SPI shift register on the
    deselection of the CPLD at the end of the SPI transaction.
    The initial state is 0 (all bits cleared).
    The bits in the configuration register (from LSB to MSB) are:

    | Name      | Width | Function                                        |
    |-----------+-------+-------------------------------------------------|
    | RF_SW     | 4     | Activates RF switch (per channel)               |
    | LED       | 4     | Activates the red LED (per channel)             |
    | PROFILE   | 4 * 3 | Controls DDS.PROFILE[0:2] (per channel)         |
    | OSK       | 4     | Asserts DDS.OSK (per channel)                   |
    | DRCTL     | 4     | Asserts DDS.DRCTL (per channel)                 |
    | DRHOLD    | 4     | Asserts DDS.DRHOLD (per channel)                |
    | IO_UPDATE | 4     | Asserts DDS.IO_UPDATE (per channel), where      |
    |           |       | CFG.MASK_NU is high                             |
    | MASK_NU   | 4     | Disables DDS from QSPI interface, disables      |
    |           |       | IO_UPDATE control through IO_UPDATE EEM signal, |
    |           |       | enables access through CS=3, enables control of |
    |           |       | IO_UPDATE through CFG.IO_UPDATE[0:3]            |
    | CLK_SEL0  | 1     | Selects CLK source: 0 MMCX/OSC, 1 SMA           |
    | SYNC_SEL  | 1     | Selects SYNC source                             |
    | RST       | 1     | Asserts DDS[0:3].RESET, DDS[0:3].MASTER_RESET,  |
    |           |       | ATT[0:3].RST                                    |
    | IO_RST    | 1     | Asserts DDS[0:3].IO_RESET                       |
    | CLK_SEL1  | 1     | Selects CLK source: 0 OSC, 1 MMCX               |
    | DIV       | 2     | Clock divider configuration: 0: default,        |
    |           |       | 1: divide-by-one, 2: divider-by-two,            |
    |           |       | 3: divide-by-four                               |
    | ATT_EN    | 4     | Enable ATT (per channel)                        |
    """

    def __init__(self, platform, n=4):
        self.data = Record(
            [
                ("rf_sw", n),
                ("led", n),
                ("profile", 3 * n),
                ("osk", n),
                ("drctl", n),
                ("drhold", n),
                ("io_update", n),
                ("mask_nu", 4),
                ("clk_sel0", 1),
                ("sync_sel", 1),
                ("rst", 1),
                ("io_rst", 1),
                ("clk_sel1", 1),
                ("div", 2),
                ("att_en", n),
            ]
        )
        dds_common = platform.lookup_request("dds_common")
        dds_sync = platform.lookup_request("dds_sync")
        att = platform.lookup_request("att")
        clk = platform.lookup_request("clk")
        self.en_9910 = Signal()

        self.comb += [
                clk.in_sel.eq(self.data.clk_sel0),
                clk.mmcx_osc_sel.eq(self.data.clk_sel1),
                clk.osc_en_n.eq(clk.in_sel | clk.mmcx_osc_sel),
                dds_sync.sync_sel.eq(self.data.sync_sel),
                dds_common.master_reset.eq(self.data.rst),
                dds_common.io_reset.eq(self.data.io_rst),
                att.rst_n.eq(~self.data.rst),
        ]

        for i in range(n):
            sw = platform.request("eem", 12 + i)
            dds = platform.lookup_request("dds", i)
            self.comb += [
                    dds.rf_sw.eq(sw.p | self.data.rf_sw[i]),
                    dds.led[0].eq(dds.rf_sw),  # green
                    dds.led[1].eq(self.data.led[i] | (self.en_9910 & (
                        dds.smp_err | ~dds.pll_lock))),  # red
                    dds.profile.eq(self.data.profile[3 * i : 3 * i + 3]),
                    dds.osk.eq(self.data.osk[i]),
                    dds.drhold.eq(self.data.drhold[i]),
                    dds.drctl.eq(self.data.drctl[i]),
            ]


class Status(Module):
    """Status register.

    The status data is loaded into the SPI shift register on the first
    rising SCK edge while the CPLD is selected. The bits from LSB to MSB
    are:

    | Name      | Width | Function                                  |
    |-----------+-------+-------------------------------------------|
    | RF_SW     | 4     | Actual RF switch and green LED activation |
    |           |       | (including that by EEM1.SW[0:3])          |
    | SMP_ERR   | 4     | DDS.SMP_ERR per channel                   |
    | PLL_LOCK  | 4     | DDS.PLL_LOCK per channel                  |
    | IFC_MODE  | 4     | IFC_MODE[0:3]                             |
    | PROTO_REV | 7     | Protocol revision (see __proto_rev__)     |
    | DROVER    | 4     | DDS.DROVER per channel                    |
    """

    def __init__(self, platform, n=4):
        self.data = Record(
            [
                ("rf_sw", n),
                ("smp_err", n),
                ("pll_lock", n),
                ("ifc_mode", 4),
                ("proto_rev", 7),
                ("drover", n),
            ]
        )
        self.comb += [
                self.data.ifc_mode.eq(platform.lookup_request("ifc_mode")),
                self.data.proto_rev.eq(__proto_rev__),
                # self.data.hw_rev.eq(platform.request("hw_rev")),
        ]
        for i in range(n):
            dds = platform.lookup_request("dds", i)
            self.comb += [
                    self.data.rf_sw[i].eq(dds.rf_sw),
                    self.data.smp_err[i].eq(dds.smp_err),
                    self.data.pll_lock[i].eq(dds.pll_lock),
                    self.data.drover[i].eq(dds.drover),
            ]


class Urukul(Module):
    """
    Urukul IO router and configuration/status
    =========================================

    The CPLD controls/monitors:

    * the four AD9912 or AD9910 DDS (SPI, status, reset, IO update)
    * the four digitally controlled RF step attenuators (SPI, reset)
    * the four RF switches
    * the clock input tree (division and clock selection)
    * the synchronization tree (sync source selection, sync clock output,
      sync drive)
    * the eight LEDs
    * the two EEM connectors
    * the test pads
    * the four configuration switches

    Pin Out
    -------

    Urukul operates from one or two EEM connectors. In standard SPI mode, the
    complete Urukul functionality can be accessed using only that interface.
    Standard SPI mode only needs the second EEM connector to interface with
    high resolution RF switching and synchronization signals. NU-Servo mode
    always requires two EEM connectors.

    | EEM  | LVDS pair | PCB net | Function                |
    |------+-----------+---------+-------------------------|
    | EEM0 | 0         | A0      | SCLK                    |
    | EEM0 | 1         | A1      | MOSI                    |
    | EEM0 | 2         | A2      | MISO, NU_CLK            |
    | EEM0 | 3         | A3      | CS0                     |
    | EEM0 | 4         | A4      | CS1                     |
    | EEM0 | 5         | A5      | CS2, NU_CS              |
    | EEM0 | 6         | A6      | IO_UPDATE               |
    | EEM0 | 7         | A7      | DDS_RESET, SYNC_OUT     |
    | EEM1 | 0         | B8      | SYNC_CLK, NU_MOSI0      |
    | EEM1 | 1         | B9      | SYNC_IN, NU_MOSI1       |
    | EEM1 | 2         | B10     | IO_UPDATE_RET, NU_MOSI2 |
    | EEM1 | 3         | B11     | NU_MOSI3                |
    | EEM1 | 4         | B12     | SW0                     |
    | EEM1 | 5         | B13     | SW1                     |
    | EEM1 | 6         | B14     | SW3                     |
    | EEM1 | 7         | B15     | SW4                     |

    IFC_MODE
    --------

    DIP switches are used to configure the operation of the Urukul CPLD. The
    four IFC mode switches are assigned as:

    | IFC_MODE | Name    | Function                                        |
    |----------+---------+-------------------------------------------------|
    | 0        | EN_9910 | On if AD9910 is populated (OR VARIANT)          |
    | 1        | EN_NU   | On if NU-Servo mode is used                     |
    | 2        | EN_EEM1 | On if the SYNC signals on EEM1 should be driven |
    | 3        | UNUSED  | Unusable on Urukul/v1.0                         |

    On Urukul/v1.0, IFC_MODE[0] | IFC_MODE[3] drive EN_9910.
    On Urukul/v1.1, IFC_MODE[0] | VARIANT (board population) drive EN_9910.

    On Urukul DIOT, second bank of DIP switches is unused.

    See :class:`Urukul`

    SPI
    ---

    An SPI interface is provided to access any of the six serial devices (the
    configuration/status SPI interface, the attenuator SPI interface, and the
    four DDS SPI interfaces). It comprises the SCLK, MOSI, MISO, CS0, CS1, and
    CS2 signals. With EN_NU, both MISO and CS2 (and the functionality provided
    by them) are unavailable. I.e. CS >= 4 (the individual DDS access) are only
    available outside of EN_NU or through CS = 3 (and CFG.MASK_NU).

    The target chip (or set of chips) is selected by CS0/CS1/CS2 (CS2 being the
    MSB). The encoding is as follows:

    | CS        | chip                                       |
    |-----------+--------------------------------------------|
    | 0 = 0b000 | None                                       |
    | 1 = 0b001 | CFG                                        |
    | 2 = 0b010 | ATT                                        |
    | 3 = 0b011 | Multiple DDS (those masked by CFG.MASK_NU) |
    | 4 = 0b100 | DDS0                                       |
    | 5 = 0b101 | DDS1                                       |
    | 6 = 0b110 | DDS2                                       |
    | 7 = 0b111 | DDS3                                       |

    The SPI interface is CPOL=0, CPHA=0, SPI mode 0, 4-wire, full fuplex. Clock
    cycles during CS[0:2] = 0 are ignored (but may still be visible on the DDS
    SCK outputs).

    See :class:`Urukul` and :class:`SR`

    CFG
    ---

    The configuration status register controls the overall operation of Urukul,
    allows some configuration options to be changed and the status of some
    signals to be monitored.

    It is 24 bits wide, MSB first.

    See :class:`SR`

    CFG write
    .........

    See :class:`CFG`

    CFG read
    ........

    See :class:`Status`

    QSPI
    ----

    If EN_NU is activated, the four DDS are additionally exposed through a
    quad-SPI write-only interface defined by the signals NU_CLK, NU_CS, and
    NU_MOSI[0:3].

    Only those DDS which are **not** masked by CFG.MASK_NU can be accessed
    through the QSPI interface. This allows initial setup and configuration of
    the DDS individually through the "regular" SPI interface in EN_NU mode.

    DDS[0:3].CS is driven by NU_CS (for those DDS not masked)
    DDS[0:3].SCK is driven by NU_CLK (for those DDS not masked)
    DDS[0:3].MOSI is driven by NU_MOSI[0:3] (for those DDS not masked)
    DDS[0:3].MISO is unavailable
    DDS[0:3].IO_UPDATE is driven by IO_UPDATE (for those DDS not masked)

    See :class:`Urukul`

    ATT
    ---

    The digital step attenuators are daisy-chained (ATT[n].S_OUT driving the
    next ATT[n+1].S_IN) and form a 32 bit SPI compatible shift register. The
    data from the attenuator shift register is transferred to the active
    attenuation register on the de-selection of the attenuators after shifting.

    Clocking
    --------

    CFG.CLK_SEL selects the clock source for the clock fanout to the DDS.
    Valid clocking options are:
        - 0x00: on-board 100MHz oscillator
        - 0x01: front-panel SMA
        - 0x02: internal MMCX (hardware version >= 1.3 only)

    For hardware revisions prior to v1.3, 0x00 selects either the on-board
    oscillator or the MMCX, dependent on component population. In these
    hardware revisions, the oscillator must be manually powered down to avoid
    RF leakage through the clock switch.

    If CFG.DIV is 0 the clock division is determined EN_9910. If it is on,
    the clock to the DDS (from the XCO, the internal MMCX or the external
    SMA) is divided by 4.

    If CFG.DIV is 1, 2, or 3 it determines the clock divisor (1, 2, 4).

    Synchronization
    ---------------

    IO_UPDATE_RET is provided to determine the round trip time for IO_UPDATE.

    DDS_RESET (not EN_9910) and SYNC_OUT (EN_9910) share an EEM signal.
    DDS_RESET provides a way to deterministically reset all AD9912 DDS SYNC_CLK
    divider. (https://ez.analog.com/docs/DOC-14472)

    SYNC_OUT is an input to the SYNC fanout (input to Urukul, output from the
    controlling FPGA upstream) to externally and actively synchronize the
    AD9910 SYNC_CLK dividers. The SYNC fanout can be driven using either
    EEM1.SYNC_OUT or DDS0.SYNC_OUT (selected by CFG.SYNC_SEL).

    SYNC_CLK and SYNC_IN are available with EN_9910 & EN_EEM1 to synchronize
    external logic to the DDS. A round-trip time measurement using
    IO_UPDATE_RET would need to be performed. SYNC_IN is an output from Urukul,
    an input to the controlling upstream FPGA, and an input to all DDS.

    RF switches
    -----------

    The RF switches are activated with CFG.RF_SW or (logic OR) SW[0:3].
    EEM1.SW[0:3] provide a high resolution and high-bandwidth port to RF
    switching.

    LEDs
    ----

    The green channel LEDs mirror the status of the RF switches. The red LEDs
    are activated by ``CFG.LED | (EN_9910 & (DDS[0:3].SMP_ERR |
    ~DDS[0:3].PLL_LOCK))``. I.e. they are lit by the register or (logic OR) an
    synchronization/PLL error on that channel's DDS.

    Test points
    -----------

    The test points expose miscellaneous signals for debugging and are not part
    of the protocol revision.
    """

    def __init__(self, platform):
        clk = platform.request("clk")
        dds_sync = platform.request("dds_sync")
        dds_common = platform.request("dds_common")
        ifc_mode = platform.request("ifc_mode", 0)
        variant = platform.request("variant")
        att = platform.request("att")
        dds = [platform.request("dds", i) for i in range(4)]
        err_led = platform.request("err")

        ts_clk_div = TSTriple()
        self.specials += [
                ts_clk_div.get_tristate(clk.div)
        ]

        self.eem = eem = [platform.request("eem", i) for i in range(12)]

        # AD9910 only
        self.clock_domains.cd_sys = ClockDomain("sys", reset_less=True)
        self.clock_domains.cd_sck0 = ClockDomain("sck0", reset_less=True)
        self.clock_domains.cd_sck1 = ClockDomain("sck1", reset_less=True)

        platform.add_period_constraint(eem[0].p, 8.)
        platform.add_period_constraint(eem[2].p, 8.)

        # SPI clock
        self.specials += Instance("SB_GB", i_USER_SIGNAL_TO_GLOBAL_BUFFER=eem[0].p, 
                                  o_GLOBAL_BUFFER_OUTPUT=self.cd_sck1.clk)

        miso_phy = Signal()
        io_update_ret = Signal()
        miso_en = Signal()
        io_update_ret_en = Signal()
        # shared with MISO
        nu_clk = Signal()
        # shared with IO_UPDATE_RET
        nu_mosi1 = Signal()
        # outputs
        self.specials += [
            # MISO
            Instance(
                "SB_IO",
                p_PIN_TYPE=C(0b100101, 6),  # output registered enabled, simple input
                p_IO_STANDARD="SB_LVCMOS",
                i_OUTPUT_CLK=ClockSignal("sck0"),
                o_PACKAGE_PIN=eem[2].p,
                i_D_OUT_0=miso_phy,
                o_D_IN_0=nu_clk,
                i_OUTPUT_ENABLE=miso_en),
            Instance(
                "SB_IO",
                p_PIN_TYPE=C(0b111100, 6),  # output registered inverted enabled
                p_IO_STANDARD="SB_LVCMOS",
                i_OUTPUT_CLK=ClockSignal("sck0"),
                o_PACKAGE_PIN=eem[2].n,
                i_D_OUT_0=miso_phy,
                i_OUTPUT_ENABLE=miso_en),
            # IO_UPDATE_RET
            Instance(
                "SB_IO",
                p_PIN_TYPE=C(0b100101, 6),  # output registered enabled, simple input
                p_IO_STANDARD="SB_LVCMOS",
                i_OUTPUT_CLK=ClockSignal("sck0"),
                o_PACKAGE_PIN=eem[10].p,
                i_D_OUT_0=io_update_ret,
                o_D_IN_0=nu_mosi1,
                i_OUTPUT_ENABLE=io_update_ret_en),
            Instance(
                "SB_IO",
                p_PIN_TYPE=C(0b111100, 6),  # output registered inverted enabled
                p_IO_STANDARD="SB_LVCMOS",
                i_OUTPUT_CLK=ClockSignal("sck0"),
                o_PACKAGE_PIN=eem[10].n,
                i_D_OUT_0=io_update_ret,
                i_OUTPUT_ENABLE=io_update_ret_en),
        ]

        en_9910 = Signal()  # AD9910 populated (instead of AD9912)
        en_nu = Signal()  # NU-Servo operation with quad SPI
        en_eem1 = Signal()  # EEM1 connected and sync outputs used

        self.comb += [
                err_led.eq(0),
                en_9910.eq(ifc_mode[0] | variant),
                en_nu.eq(ifc_mode[1]),
                en_eem1.eq(ifc_mode[2]),
                miso_en.eq(~en_nu),
                io_update_ret_en.eq(~en_nu & en_eem1),
                io_update_ret.eq(eem[6].p),
                self.cd_sck0.clk.eq(~self.cd_sck1.clk),
                dds_sync.clk_out_en.eq(~en_nu & en_eem1 & en_9910),
                dds_sync.sync_out_en.eq(~en_nu & en_eem1 & en_9910),
        ]

        cfg = CFG(platform)
        stat = Status(platform)
        sr = SR(52)
        assert len(cfg.data) <= len(sr.di)
        assert len(stat.data) <= len(sr.do)
        self.submodules += cfg, stat, sr

        sel = Signal(8)
        cs = Signal(3)
        miso = Signal(8)
        mosi = eem[1].p

        self.specials += [
            Instance("SB_DFFES", i_D=0, i_C=ClockSignal("sck1"), i_E=sel[2],
                     i_S=~(sel[2] & cfg.data.att_en[i]), o_Q=att.le[i]) for i in range(4)
        ]

        self.comb += [
                cfg.en_9910.eq(en_9910),
                cs.eq(Cat(eem[3].p, eem[4].p, ~en_nu & eem[5].p)),
                Array(sel)[cs].eq(1),  # one-hot
                miso_phy.eq(Array(miso)[cs]),
                miso[3].eq(miso[4]),  # for all-DDS take DDS0:MISO

                att.clk.eq(sel[2] & self.cd_sck1.clk),
                Cat(att.s_in, miso[2]).eq(Cat(mosi, att.s_out)),

                sr.sel.eq(sel[1]),
                sr.sdi.eq(mosi),
                miso[1].eq(sr.sdo),

                cfg.data.raw_bits().eq(sr.di),
                sr.do.eq(stat.data.raw_bits()),

                # dividers: z: 1, 0: 2, 1: 4
                # 1: div-by-4 for AD9910
                # z: div-by-1 for AD9912
                ts_clk_div.oe.eq(Array([en_9910, 0, 1, 1])[cfg.data.div]),
                ts_clk_div.o.eq(Array([1, 1, 0, 1])[cfg.data.div]),
        ]
        for i, ddsi in enumerate(dds):
            sel_spi = Signal()
            sel_nu = Signal()
            if i == 2:
                self.comb += [ddsi.sdi.eq(Mux(sel_nu, nu_mosi1, mosi))]
            else:
                self.comb += [ddsi.sdi.eq(Mux(sel_nu, eem[i + 8].p, mosi))]
            self.comb += [
                    sel_spi.eq(sel[i + 4] | (sel[3] & cfg.data.mask_nu[i])),
                    sel_nu.eq(en_nu & ~cfg.data.mask_nu[i]),
                    ddsi.cs_n.eq(~Mux(sel_nu, eem[5].p, sel_spi)),
                    ddsi.sck.eq(Mux(sel_nu, nu_clk, self.cd_sck1.clk)),
                    miso[i + 4].eq(ddsi.sdo),
                    ddsi.io_update.eq(Mux(cfg.data.mask_nu[i],
                        cfg.data.io_update, eem[6].p)),
                    ddsi.reset.eq(cfg.data.rst | (~en_9910 & eem[7].p)),
            ]

        tp = [platform.request("tp", i) for i in range(5)]
        self.comb += [
                tp[0].eq(dds[0].cs_n),
                tp[1].eq(dds[0].sck),
                tp[2].eq(dds[0].sdi),
                tp[3].eq(dds[0].sdo),
                tp[4].eq(dds[0].drover),
        ]

if __name__ == "__main__":
    from urukul_cpld_ice import Platform
    platform = Platform()
    platform.toolchain.nextpnr_build_template[1:2] = [
        "for seed in `seq 1 10`; do",
        "echo Seed $seed",
        ("nextpnr-ice40 {pnr_pkg_opts} --pcf {build_name}.pcf --json {build_name}.json "
        "--asc {build_name}.txt --pre-pack {build_name}_pre_pack.py --seed $seed && break"),
        "done"
    ]
    urukul = Urukul(platform)
    platform.build(urukul, build_name="urukul")
