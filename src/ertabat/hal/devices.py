"""Device specifications — enough for another agent to write a driver blind.

Ranges and rates are the figures each vendor publishes for the product; where a
figure is variant-dependent or not published it is listed in `unknowns` rather
than filled in. Nothing here is a benchmark: none of these has been measured on
this bench, and the suite says so.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

from .base import DeviceSpec

M = 1e6
G = 1e9

SPECS = {
    "rtlsdr-v3": DeviceSpec(
        "rtlsdr-v3", "RTL-SDR Blog V3", "RTL-SDR Blog",
        500e3, 1.766 * G, 2.4 * M, 8, False, False, "usb2", "librtlsdr",
        notes="receive only; direct-sampling mode below 24 MHz; needs a "
              "downconverter or LNB for anything above L-band",
        unknowns=("measured noise figure on this bench",)),
    "nesdr-xtr": DeviceSpec(
        "nesdr-xtr", "NooElec NESDR XTR", "NooElec",
        65e6, 2.3 * G, 2.4 * M, 8, False, False, "usb2", "librtlsdr",
        notes="E4000 tuner: wider top end than R820T, with a gap around 1.1 GHz",
        unknowns=("exact tuner gap edges per unit",)),
    "hackrf-one": DeviceSpec(
        "hackrf-one", "HackRF One", "Great Scott Gadgets",
        1 * M, 6 * G, 20 * M, 8, False, True, "usb2", "libhackrf",
        notes="half duplex; transmit is real but 8-bit and unfiltered — "
              "a filter and an amplifier are not optional on air"),
    "adalm-pluto": DeviceSpec(
        "adalm-pluto", "ADALM-PLUTO", "Analog Devices",
        325 * M, 3.8 * G, 61.44 * M, 12, True, True, "usb2", "libiio",
        notes="AD9363 part; the widely used firmware retune to 70 MHz–6 GHz is "
              "out of specification, not a rating"),
    "usrp-b210": DeviceSpec(
        "usrp-b210", "Ettus USRP B210", "Ettus Research / NI",
        70 * M, 6 * G, 61.44 * M, 12, True, True, "usb3", "UHD",
        notes="2x2 MIMO; the reference platform for srsRAN and OpenAirInterface "
              "testbeds; GPSDO fitted as an option and needed for NTN timing"),
    "usrp-x310": DeviceSpec(
        "usrp-x310", "Ettus USRP X310", "Ettus Research / NI",
        10 * M, 6 * G, 200 * M, 14, True, True, "ethernet", "UHD",
        notes="daughterboard-dependent coverage; 10 GbE host link",
        unknowns=("installed daughterboard determines the real tuning range",)),
    "limesdr-usb": DeviceSpec(
        "limesdr-usb", "LimeSDR USB", "Lime Microsystems",
        100e3, 3.8 * G, 61.44 * M, 12, True, True, "usb3", "LimeSuite"),
    "lnb-ku-universal": DeviceSpec(
        "lnb-ku-universal", "Universal Ku-band LNBF (downconverter)", "generic",
        10.7 * G, 12.75 * G, 0.0, 0, False, False, "coax", "none (analogue)",
        notes="RECEIVE-ONLY block downconverter. It is not a radio and not a "
              "payload: it converts Ku to an L-band IF for an SDR behind a "
              "bias tee. Consumer DTH parts are unqualified for vacuum or "
              "thermal cycling and the local oscillator is uncontrolled.",
        unknowns=("LO stability over temperature", "phase noise")),
    "flight-sdr-class": DeviceSpec(
        "flight-sdr-class", "Space-qualified FPGA SDR payload (class)", "several",
        100 * M, 18 * G, 100 * M, 12, True, True, "spacewire/lvds",
        "vendor SDK", space_grade="rad-tolerant",
        notes="A CLASS, not a product. Real parts differ in every figure here; "
              "bind a specific datasheet before this line is used in a budget.",
        unknowns=("total ionising dose rating", "power draw at duty",
                  "published tuning range per part", "SEU mitigation scheme")),
}


def by_frequency(freq_hz: float):
    return [s for s in SPECS.values() if s.covers(freq_hz)]


def transmit_capable():
    return [s for s in SPECS.values() if s.transmit]
