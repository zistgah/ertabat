"""Orbit geometry, Doppler and pass dynamics.

Circular-orbit two-body model, stated plainly: it is exact for a circular orbit
and a coplanar station, and it is NOT an ephemeris. Where a real pass is needed,
supply a TLE and an SGP4 propagator (see `propagate_tle`), which declares itself
absent rather than approximating.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import math

from .. import Unknown

MU_EARTH = 398600.4418        # km^3/s^2
R_EARTH = 6378.137            # km
C_KM_S = 299792.458
OMEGA_EARTH = 7.2921159e-5    # rad/s


def orbital_velocity_km_s(altitude_km: float) -> float:
    return math.sqrt(MU_EARTH / (R_EARTH + altitude_km))


def mean_motion_rad_s(altitude_km: float) -> float:
    r = R_EARTH + altitude_km
    return math.sqrt(MU_EARTH / r ** 3)


def orbital_period_s(altitude_km: float) -> float:
    return 2 * math.pi / mean_motion_rad_s(altitude_km)


def max_range_rate_km_s(altitude_km: float) -> float:
    """Worst-case radial rate, at the horizon of a coplanar overhead pass.

    d^2 = r^2 + Re^2 - 2 r Re cos(theta); differentiate and evaluate at the
    horizon (cos theta = Re/r). It reduces exactly to Re * n.
    """
    return R_EARTH * mean_motion_rad_s(altitude_km)


def doppler_shift_hz(freq_hz: float, range_rate_km_s: float) -> float:
    return -freq_hz * (range_rate_km_s / C_KM_S)


def max_doppler_hz(freq_hz: float, altitude_km: float) -> float:
    return abs(doppler_shift_hz(freq_hz, max_range_rate_km_s(altitude_km)))


def max_doppler_rate_hz_s(freq_hz: float, altitude_km: float, min_range_km=None) -> float:
    """Peak df/dt, at closest approach: a = v_t^2 / d_min."""
    d = altitude_km if min_range_km is None else min_range_km
    v = orbital_velocity_km_s(altitude_km) - R_EARTH * OMEGA_EARTH
    return abs(freq_hz * (v * v / d) / C_KM_S)


def pass_duration_s(altitude_km: float, min_elevation_deg: float = 10.0,
                    include_earth_rotation: bool = True):
    """Horizon-to-horizon visibility for the best (overhead) coplanar pass."""
    r = R_EARTH + altitude_km
    e = math.radians(min_elevation_deg)
    arg = R_EARTH * math.cos(e) / r
    if not -1.0 <= arg <= 1.0:
        return Unknown("pass duration: geometry has no solution at this elevation")
    half = math.acos(arg) - e
    n = mean_motion_rad_s(altitude_km)
    rel = (n - OMEGA_EARTH) if include_earth_rotation else n
    return 2 * half / rel


def ground_track_speed_km_s(altitude_km: float) -> float:
    return R_EARTH * (mean_motion_rad_s(altitude_km) - OMEGA_EARTH)


def beam_dwell_s(altitude_km: float, beam_diameter_km: float) -> float:
    """How long a fixed user stays inside a moving spot beam.

    This, not the visibility window, is the handover clock in an NTN.
    """
    return beam_diameter_km / ground_track_speed_km_s(altitude_km)


def beam_diameter_km(altitude_km: float, beamwidth_deg: float) -> float:
    return 2 * altitude_km * math.tan(math.radians(beamwidth_deg) / 2.0)


def propagate_tle(tle_line1: str, tle_line2: str, when_utc):
    """Real ephemeris. Uses python-sgp4 if installed; otherwise declares absence.

    No fallback approximation is offered here on purpose: a two-body circle
    presented as a propagated TLE is a fabrication with a plausible shape.
    """
    try:
        from sgp4.api import Satrec, jday  # type: ignore
    except Exception:
        return Unknown("SGP4 propagator not installed",
                       ("pip install sgp4", "or supply an ephemeris table"))
    sat = Satrec.twoline2rv(tle_line1, tle_line2)
    jd, fr = jday(when_utc.year, when_utc.month, when_utc.day,
                  when_utc.hour, when_utc.minute,
                  when_utc.second + when_utc.microsecond / 1e6)
    err, pos, vel = sat.sgp4(jd, fr)
    if err:
        return Unknown(f"SGP4 error code {err}")
    return {"position_km": pos, "velocity_km_s": vel}
