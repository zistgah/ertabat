"""Link budget — the arithmetic every other claim in this repo has to survive.

All losses are POSITIVE decibels and subtracted. Nothing defaults to zero: an
absent term is Unknown and poisons the result, by design.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

from .. import Unknown, known, require

BOLTZMANN_DBW = -228.6  # dBW/K/Hz, 10*log10(1.380649e-23), rounded per convention
C_KM_S = 299792.458


def fspl_db(distance_km: float, freq_mhz: float):
    """Free-space path loss. 20log d(km) + 20log f(MHz) + 32.44778."""
    if distance_km is None or freq_mhz is None:
        return Unknown("free-space path loss", ("distance_km", "freq_mhz"))
    if distance_km <= 0 or freq_mhz <= 0:
        return Unknown("free-space path loss needs positive distance and frequency")
    return 20 * math.log10(distance_km) + 20 * math.log10(freq_mhz) + 32.4477832


def slant_range_km(altitude_km: float, elevation_deg: float, earth_radius_km: float = 6378.137):
    """Slant range to a satellite at `altitude_km` seen at `elevation_deg`."""
    if altitude_km is None or elevation_deg is None:
        return Unknown("slant range", ("altitude_km", "elevation_deg"))
    re = earth_radius_km
    r = re + altitude_km
    e = math.radians(elevation_deg)
    return math.sqrt(r * r - (re * math.cos(e)) ** 2) - re * math.sin(e)


def g_over_t_db(gain_dbi: float, system_noise_temp_k: float):
    if gain_dbi is None or system_noise_temp_k is None or system_noise_temp_k <= 0:
        return Unknown("G/T", ("gain_dbi", "system_noise_temp_k"))
    return gain_dbi - 10 * math.log10(system_noise_temp_k)


def system_noise_temp_k(antenna_temp_k: float, receiver_nf_db: float, feed_loss_db: float = 0.0,
                        reference_k: float = 290.0):
    """T_sys referred to the antenna port, through a lossy feed."""
    if antenna_temp_k is None or receiver_nf_db is None:
        return Unknown("system noise temperature", ("antenna_temp_k", "receiver_nf_db"))
    l = 10 ** (feed_loss_db / 10.0)
    t_feed = reference_k * (l - 1)
    t_rx = reference_k * (10 ** (receiver_nf_db / 10.0) - 1)
    return antenna_temp_k + t_feed + t_rx


@dataclass
class LinkResult:
    eirp_dbw: object
    fspl_db: object
    atmospheric_loss_db: object
    pointing_loss_db: object
    g_over_t_db: object
    c_over_n0_dbhz: object
    eb_over_n0_db: object
    required_eb_over_n0_db: object
    implementation_loss_db: float
    margin_db: object

    def as_dict(self):
        d = asdict(self)
        return {k: (str(v) if isinstance(v, Unknown) else v) for k, v in d.items()}

    def closes(self) -> bool:
        return known(self.margin_db) and self.margin_db > 0


def link_budget(*, tx_power_dbw, tx_gain_dbi, tx_line_loss_db=0.0,
                distance_km=None, freq_mhz=None,
                atmospheric_loss_db=None, pointing_loss_db=0.0,
                rx_gain_dbi=None, system_noise_temp_k=None,
                data_rate_bps=None, required_eb_over_n0_db=None,
                implementation_loss_db=2.0) -> LinkResult:
    """One pass of the standard budget. Unknowns propagate to the margin.

    atmospheric_loss_db has NO default. A budget computed with the atmosphere
    silently set to zero is the commonest way a paper link closes and a real one
    does not; ertabat.link.atmosphere supplies it, or the caller declares it.
    """
    eirp = (tx_power_dbw + tx_gain_dbi - tx_line_loss_db
            if None not in (tx_power_dbw, tx_gain_dbi) else
            Unknown("EIRP", ("tx_power_dbw", "tx_gain_dbi")))
    fspl = fspl_db(distance_km, freq_mhz)
    atm = Unknown("atmospheric loss", ("atmospheric_loss_db",)) \
        if atmospheric_loss_db is None else atmospheric_loss_db
    gt = g_over_t_db(rx_gain_dbi, system_noise_temp_k)

    miss = require(eirp=eirp, fspl=fspl, atm=atm, gt=gt)
    cn0 = miss if miss is not None else (eirp - fspl - atm - pointing_loss_db + gt - BOLTZMANN_DBW)

    if known(cn0) and data_rate_bps:
        ebn0 = cn0 - 10 * math.log10(data_rate_bps)
    elif not known(cn0):
        ebn0 = cn0
    else:
        ebn0 = Unknown("Eb/N0", ("data_rate_bps",))

    if known(ebn0) and required_eb_over_n0_db is not None and known(required_eb_over_n0_db):
        margin = ebn0 - required_eb_over_n0_db - implementation_loss_db
    else:
        margin = ebn0 if not known(ebn0) else Unknown(
            "margin", ("required_eb_over_n0_db",))

    return LinkResult(eirp, fspl, atm, pointing_loss_db, gt, cn0, ebn0,
                      required_eb_over_n0_db, implementation_loss_db, margin)
