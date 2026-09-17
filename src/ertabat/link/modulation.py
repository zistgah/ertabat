"""Required Eb/N0, DERIVED rather than recalled.

Textbook tables are the usual source of these numbers and a remembered table is
a hypothesis, not a retrieval. So the AWGN bit-error expressions are inverted
numerically here: the number you get is one you can re-derive from the formula
printed beside it. Coded thresholds are NOT derived — a code's threshold depends
on its construction, so those return Unknown until a measured or cited value is
supplied.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import math

from .. import Unknown

SQRT2 = math.sqrt(2.0)


def q(x: float) -> float:
    """Gaussian tail Q(x) = 0.5 erfc(x/sqrt 2)."""
    return 0.5 * math.erfc(x / SQRT2)


def ber_awgn(scheme: str, ebn0_db: float):
    """Uncoded AWGN bit-error probability, coherent detection, Gray mapping.

    BPSK/QPSK : Q(sqrt(2 Eb/N0))
    M-PSK     : (2/k) Q(sqrt(2 k Eb/N0) sin(pi/M))          k = log2 M
    M-QAM     : (4/k)(1 - 1/sqrt M) Q(sqrt(3 k Eb/N0/(M-1)))
    """
    s = scheme.strip().upper().replace("-", "")
    g = 10 ** (ebn0_db / 10.0)
    if s in ("BPSK", "QPSK", "4QAM"):
        return q(math.sqrt(2 * g))
    if s.endswith("PSK"):
        m = int(s[:-3]); k = int(math.log2(m))
        return (2.0 / k) * q(math.sqrt(2 * k * g) * math.sin(math.pi / m))
    if s.endswith("QAM"):
        m = int(s[:-3]); k = int(math.log2(m))
        return (4.0 / k) * (1 - 1 / math.sqrt(m)) * q(math.sqrt(3 * k * g / (m - 1)))
    return Unknown(f"no closed-form BER carried for {scheme}", ("ber_expression",))


def required_ebn0_db(scheme: str, target_ber: float = 1e-5, coding=None):
    """Invert ber_awgn by bisection. `coding` must be a declared gain in dB."""
    probe = ber_awgn(scheme, 10.0)
    if isinstance(probe, Unknown):
        return probe
    lo, hi = -10.0, 60.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if ber_awgn(scheme, mid) > target_ber:
            lo = mid
        else:
            hi = mid
    uncoded = (lo + hi) / 2.0
    if coding is None:
        return uncoded
    if isinstance(coding, Unknown):
        return coding
    return uncoded - float(coding)


def spectral_efficiency(scheme: str, code_rate=None):
    s = scheme.strip().upper().replace("-", "")
    try:
        m = 2 if s == "BPSK" else (4 if s == "QPSK" else int(s[:-3]))
        k = math.log2(m)
    except ValueError:
        return Unknown(f"symbol order not parseable from {scheme}")
    if code_rate is None:
        return Unknown("spectral efficiency", ("code_rate",))
    return k * float(code_rate)


def symbol_rate(bit_rate_bps: float, scheme: str, code_rate=None):
    se = spectral_efficiency(scheme, code_rate)
    if isinstance(se, Unknown):
        return se
    return bit_rate_bps / se


CODED_THRESHOLDS_NOTE = (
    "Coded thresholds (LDPC/turbo/convolutional, DVB-S2X MODCODs, CCSDS 131.0-B) "
    "are not carried in this module. Supply `coding=<measured or cited dB>` or "
    "populate data/modcod.json; an absent threshold stays Unknown."
)
