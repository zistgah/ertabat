"""Atmospheric loss — the term this repo refuses to guess.

Rain attenuation needs the ITU-R P.838 k/alpha coefficients and the P.618 path
model; gaseous absorption needs P.676; scintillation needs the P.453 wet-term
refractivity for the site. Those are published tables. Carrying them from
memory is exactly the failure this estate has a clause about, so the tables are
loaded from `data/itu_p838.json` and `data/itu_p676.json` and are shipped EMPTY.

Populate them from the ITU-R recommendation text and every function below
starts returning numbers. Until then each returns Unknown naming the file and
the recommendation. `ertabat dispatch` emits this as a work packet with its own
acceptance test.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import json
import math
import os

from .. import Unknown

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "data"))

SCHEMA_P838 = {
    "recommendation": "ITU-R P.838-3",
    "columns": ["freq_ghz", "k_h", "alpha_h", "k_v", "alpha_v"],
    "rows": [],
    "populated_by": "",
    "retrieved_utc": "",
}
SCHEMA_P676 = {
    "recommendation": "ITU-R P.676",
    "columns": ["freq_ghz", "gamma_o_db_km", "gamma_w_db_km_per_g_m3"],
    "rows": [],
    "populated_by": "",
    "retrieved_utc": "",
}


def _load(name: str, schema: dict):
    path = os.path.join(_DATA, name)
    if not os.path.exists(path):
        return Unknown(f"{schema['recommendation']} table absent",
                       (f"data/{name}", schema["recommendation"]))
    try:
        with open(path) as fh:
            d = json.load(fh)
    except Exception as exc:                      # a corrupt table is not an empty one
        return Unknown(f"{name} unreadable: {exc}", (f"data/{name}",))
    if not d.get("rows"):
        return Unknown(f"{schema['recommendation']} table present but empty",
                       (f"data/{name}", schema["recommendation"]))
    if not d.get("retrieved_utc") or not d.get("populated_by"):
        return Unknown(f"{name} carries no provenance — who populated it, and when",
                       ("populated_by", "retrieved_utc"))
    return d


def _interp(rows, freq_ghz, ci):
    xs = sorted(rows, key=lambda r: r[0])
    if freq_ghz < xs[0][0] or freq_ghz > xs[-1][0]:
        return Unknown(f"{freq_ghz} GHz is outside the loaded table "
                       f"({xs[0][0]}–{xs[-1][0]} GHz) — extrapolation is invention")
    for a, b in zip(xs, xs[1:]):
        if a[0] <= freq_ghz <= b[0]:
            if b[0] == a[0]:
                return a[ci]
            # P.838 prescribes log-log interpolation for k, linear for alpha
            if ci in (1, 3):
                t = (math.log(freq_ghz) - math.log(a[0])) / (math.log(b[0]) - math.log(a[0]))
                return math.exp(math.log(a[ci]) + t * (math.log(b[ci]) - math.log(a[ci])))
            t = (freq_ghz - a[0]) / (b[0] - a[0])
            return a[ci] + t * (b[ci] - a[ci])
    return Unknown("interpolation failed")


def specific_rain_attenuation_db_km(freq_ghz, rain_rate_mm_h, polarisation="circular",
                                    elevation_deg=None, tilt_deg=None):
    """gamma_R = k R^alpha, with k/alpha from the loaded P.838 table."""
    tab = _load("itu_p838.json", SCHEMA_P838)
    if isinstance(tab, Unknown):
        return tab
    kh = _interp(tab["rows"], freq_ghz, 1); ah = _interp(tab["rows"], freq_ghz, 2)
    kv = _interp(tab["rows"], freq_ghz, 3); av = _interp(tab["rows"], freq_ghz, 4)
    for v in (kh, ah, kv, av):
        if isinstance(v, Unknown):
            return v
    p = polarisation.lower()
    if p.startswith("h"):
        k, a = kh, ah
    elif p.startswith("v"):
        k, a = kv, av
    else:
        if elevation_deg is None:
            return Unknown("circular polarisation needs the path elevation",
                           ("elevation_deg",))
        t = math.radians(45.0 if tilt_deg is None else tilt_deg)
        th = math.radians(elevation_deg)
        k = (kh + kv + (kh - kv) * math.cos(th) ** 2 * math.cos(2 * t)) / 2
        a = (kh * ah + kv * av + (kh * ah - kv * av) * math.cos(th) ** 2 * math.cos(2 * t)) / (2 * k)
    return k * (rain_rate_mm_h ** a)


def rain_attenuation_db(freq_ghz, elevation_deg, rain_rate_mm_h,
                        station_height_km=0.0, rain_height_km=None,
                        polarisation="circular", tilt_deg=None):
    """P.618 slant-path rain attenuation. Needs the rain height for the site."""
    if rain_height_km is None:
        return Unknown("rain height for this site",
                       ("rain_height_km", "ITU-R P.839"))
    g = specific_rain_attenuation_db_km(freq_ghz, rain_rate_mm_h, polarisation,
                                        elevation_deg, tilt_deg)
    if isinstance(g, Unknown):
        return g
    e = math.radians(elevation_deg)
    if elevation_deg < 5:
        return Unknown("P.618 slant path below 5 degrees needs the full "
                       "earth-curvature form, which is not implemented here")
    ls = (rain_height_km - station_height_km) / math.sin(e)
    lg = ls * math.cos(e)
    r = 1.0 / (1.0 + 0.78 * math.sqrt(lg * g / freq_ghz) - 0.38 * (1 - math.exp(-2 * lg)))
    return g * ls * r


def gaseous_absorption_db(freq_ghz, elevation_deg, water_vapour_g_m3=None):
    tab = _load("itu_p676.json", SCHEMA_P676)
    if isinstance(tab, Unknown):
        return tab
    if water_vapour_g_m3 is None:
        return Unknown("gaseous absorption", ("water_vapour_g_m3",))
    go = _interp(tab["rows"], freq_ghz, 1); gw = _interp(tab["rows"], freq_ghz, 2)
    for v in (go, gw):
        if isinstance(v, Unknown):
            return v
    return (go * 5.0 + gw * water_vapour_g_m3 * 2.0) / math.sin(math.radians(elevation_deg))


def scintillation_fade_db(freq_ghz, elevation_deg, antenna_diameter_m,
                          n_wet=None, availability_pct=99.9):
    if n_wet is None:
        return Unknown("tropospheric scintillation", ("n_wet", "ITU-R P.453"))
    return Unknown("P.618 scintillation model not implemented — "
                   "packet ATM-3 carries its acceptance test")


def ionospheric_scintillation_index(freq_ghz, geomagnetic_latitude_deg,
                                    local_time_hour, solar_flux_index=None):
    """S4 index. Climatological, and honestly outside a closed-form here."""
    return Unknown("ionospheric S4 needs a climatology model (ITU-R P.531) "
                   "or measured data", ("p531_table", "or measured S4"))


def total_atmospheric_loss_db(**kw):
    """Sum the terms — and refuse if any one of them is Unknown."""
    parts, missing = {}, []
    for name, fn, args in (
        ("rain", rain_attenuation_db, ("freq_ghz", "elevation_deg", "rain_rate_mm_h",
                                       "station_height_km", "rain_height_km",
                                       "polarisation", "tilt_deg")),
        ("gas", gaseous_absorption_db, ("freq_ghz", "elevation_deg", "water_vapour_g_m3")),
    ):
        v = fn(**{k: kw[k] for k in args if k in kw})
        parts[name] = v
        if isinstance(v, Unknown):
            missing.append(f"{name}: {v}")
    if missing:
        return Unknown("total atmospheric loss incomplete", tuple(missing))
    return sum(parts.values())
