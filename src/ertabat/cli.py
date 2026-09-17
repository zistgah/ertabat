"""ertabat — one command surface over the whole spine.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import Unknown, __version__, known
from .link import atmosphere, budget, geometry, modulation
from .ntn import duplex, oran, timing
from .hal import devices as hal_devices
from .hal import registry as hal_registry
from .sota import registry as sota
from . import dispatch

BANNER = "ertabat %s · © 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI." % __version__


def _out(obj, as_json):
    if as_json:
        def enc(o):
            if isinstance(o, Unknown):
                return {"unknown": o.reason, "needs": list(o.needs)}
            if hasattr(o, "as_dict"):
                return o.as_dict()
            return str(o)
        print(json.dumps(obj, default=enc, indent=2))
        return
    if isinstance(obj, dict):
        w = max((len(str(k)) for k in obj), default=0)
        for k, v in obj.items():
            print(f"  {str(k):<{w}}  {v}")
    elif isinstance(obj, list):
        for v in obj:
            print(f"  {v}")
    else:
        print(f"  {obj}")


def cmd_link(a):
    d = a.distance_km
    if d is None and a.altitude_km is not None:
        d = budget.slant_range_km(a.altitude_km, a.elevation_deg)
    req = a.required_ebn0_db
    if req is None and a.modulation:
        req = modulation.required_ebn0_db(a.modulation, a.target_ber, a.coding_gain_db)
    r = budget.link_budget(
        tx_power_dbw=a.tx_power_dbw, tx_gain_dbi=a.tx_gain_dbi,
        tx_line_loss_db=a.tx_line_loss_db, distance_km=d, freq_mhz=a.freq_mhz,
        atmospheric_loss_db=a.atmospheric_loss_db, pointing_loss_db=a.pointing_loss_db,
        rx_gain_dbi=a.rx_gain_dbi, system_noise_temp_k=a.system_noise_temp_k,
        data_rate_bps=a.data_rate_bps, required_eb_over_n0_db=req,
        implementation_loss_db=a.implementation_loss_db)
    out = r.as_dict()
    out["distance_km"] = d
    out["modulation"] = a.modulation or "-"
    out["closes"] = r.closes()
    _out(out, a.json)
    return 0 if r.closes() else 3


def cmd_pass(a):
    f = a.freq_mhz * 1e6
    out = {
        "altitude_km": a.altitude_km,
        "orbital_velocity_km_s": round(geometry.orbital_velocity_km_s(a.altitude_km), 4),
        "period_min": round(geometry.orbital_period_s(a.altitude_km) / 60, 2),
        "max_range_rate_km_s": round(geometry.max_range_rate_km_s(a.altitude_km), 4),
        "max_doppler_hz": round(geometry.max_doppler_hz(f, a.altitude_km), 1),
        "max_doppler_rate_hz_s": round(geometry.max_doppler_rate_hz_s(f, a.altitude_km), 2),
        "pass_duration_s": round(geometry.pass_duration_s(a.altitude_km, a.elevation_deg), 1),
        "slant_range_km": round(budget.slant_range_km(a.altitude_km, a.elevation_deg), 1),
    }
    if a.beamwidth_deg:
        bd = geometry.beam_diameter_km(a.altitude_km, a.beamwidth_deg)
        out["beam_diameter_km"] = round(bd, 1)
        out["beam_dwell_s"] = round(geometry.beam_dwell_s(a.altitude_km, bd), 1)
        out.update(timing.handover_cadence_s(geometry.beam_dwell_s(a.altitude_km, bd)))
    _out(out, a.json)
    return 0


def cmd_ntn(a):
    d_far = budget.slant_range_km(a.altitude_km, a.elevation_deg)
    d_near = budget.slant_range_km(a.altitude_km, 90.0)
    b = timing.delay_budget(d_far, feeder_link_km=a.feeder_link_km,
                            architecture=a.architecture, service_link_min_km=d_near)
    if isinstance(b, Unknown):
        _out(b, a.json)
        return 4
    out = {
        "architecture": b.architecture,
        "slant_range_km": round(d_far, 1),
        "one_way_ms": round(b.one_way_ms, 3),
        "rtt_ms": round(b.rtt_ms, 3),
        "differential_ms": round(b.differential_ms, 3),
        "k_offset_slots": timing.k_offset_slots(b.rtt_ms, a.numerology),
        "slot_ms": timing.slot_duration_ms(a.numerology),
    }
    out.update({f"harq_{k}": v for k, v in
                timing.harq_verdict(b.rtt_ms, timing.slot_duration_ms(a.numerology),
                                    a.harq_processes).items()})
    out.update({f"prach_{k}": v for k, v in
                timing.prach_verdict(b.differential_ms, a.preamble_format,
                                     a.cyclic_prefix_us, a.gnss).items()})
    out.update({f"duplex_{k}": v for k, v in
                duplex.duplex_verdict(b.differential_ms, a.guard_period_us).items()})
    _out(out, a.json)
    return 0


def cmd_oran(a):
    kw = {"sample_rate_msps": a.sample_rate_msps, "antenna_ports": a.antenna_ports,
          "bits_per_sample": a.bits_per_sample, "used_subcarriers": a.used_subcarriers,
          "symbols_per_second": a.symbols_per_second,
          "user_throughput_bps": a.user_throughput_bps}
    kw = {k: v for k, v in kw.items() if v is not None}
    res = oran.split_verdict(a.split, feeder_capacity_bps=a.feeder_capacity_bps, **kw)
    _out(res, a.json)
    if isinstance(res, Unknown):
        return 4
    return 0 if res.get("fits_feeder", True) else 3


def cmd_hal(a):
    if a.device:
        dev = hal_registry.open_device(a.device)
        if isinstance(dev, Unknown):
            _out(dev, a.json)
            return 4
        _out(dev.self_describe(), a.json)
        return 0
    if a.freq_mhz:
        specs = hal_devices.by_frequency(a.freq_mhz * 1e6)
        _out([f"{s.key:<18} {s.display_name} ({'TX+RX' if s.transmit else 'RX only'})"
              for s in specs] or ["no carried device covers that frequency"], a.json)
        return 0
    _out(hal_registry.census(), a.json)
    return 0


def cmd_sota(a):
    if a.promote:
        r = sota.promote_check(a.promote, a.to, a.evidence)
        _out(r, a.json)
        return 4 if isinstance(r, Unknown) else 0
    if a.track:
        t = sota.TRACKS.get(a.track)
        _out(t.as_dict() if t else Unknown(f"no track {a.track}", tuple(sota.TRACKS)), a.json)
        return 0 if t else 4
    _out({k: f"{v.status:<10} {v.title}" for k, v in sota.TRACKS.items()}, a.json)
    return 0


def cmd_bom(a):
    from .bom.lookup import Cache, PriceService, load_fx
    from .bom.model import parse_csv
    from .bom.report import to_csv, to_markdown
    if not os.path.exists(a.file):
        print(f"  no such BoM: {a.file}", file=sys.stderr)
        return 2
    lines = parse_csv(open(a.file).read())
    svc = PriceService(order=a.providers.split(",") if a.providers else None or
                       ("local", "nexar", "mouser", "element14", "digikey", "lcsc"),
                       cache=Cache(path=a.cache, ttl_s=a.cache_ttl_s),
                       price_book=a.price_book, currency=a.currency)
    if a.status:
        _out(svc.status(), a.json)
        return 0
    fx = load_fx(a.fx)
    priced, tot = svc.price_bom(lines, use_cache=not a.no_cache, fx=fx)
    if a.json:
        _out({"lines": [{"ref": p.line.ref, "mpn": p.line.mpn, "qty": p.line.qty,
                         "quote": p.quote} for p in priced], "totals": tot}, True)
    else:
        print(to_markdown(priced, tot, title=f"BoM · {os.path.basename(a.file)}"))
    if a.out_md:
        open(a.out_md, "w").write(to_markdown(priced, tot))
    if a.out_csv:
        open(a.out_csv, "w").write(to_csv(priced))
    return 0 if tot["lines_unpriced"] == 0 else 3


def cmd_dispatch(a):
    if a.json:
        print(dispatch.to_json())
    else:
        print(dispatch.to_markdown())
    if a.out:
        open(a.out, "w").write(dispatch.to_markdown())
    return 0


def cmd_doctor(a):
    from .bom.lookup import PriceService
    rows = {
        "python": sys.version.split()[0],
        "sgp4 propagator": "present" if _has("sgp4") else "absent — TLE propagation declares itself",
        "P.838 rain table": "present" if os.path.exists("data/itu_p838.json") else "absent — high-band budgets return Unknown",
        "P.676 gas table": "present" if os.path.exists("data/itu_p676.json") else "absent",
        "bound radio drivers": ", ".join(hal_registry.bound_drivers()) or "none — every device is a stub",
    }
    for s in PriceService().status():
        rows[f"price provider {s['provider']}"] = "ready" if s["available"] else s["reason"]
    _out(rows, a.json)
    return 0


def _has(mod):
    try:
        __import__(mod)
        return True
    except Exception:
        return False


def build_parser():
    p = argparse.ArgumentParser("ertabat", description=BANNER)
    p.add_argument("--version", action="version", version=BANNER)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(x):
        x.add_argument("--json", action="store_true", help="machine-readable output")
        return x

    l = common(sub.add_parser("link", help="link budget"))
    l.add_argument("--tx-power-dbw", type=float, required=True)
    l.add_argument("--tx-gain-dbi", type=float, required=True)
    l.add_argument("--tx-line-loss-db", type=float, default=0.0)
    l.add_argument("--rx-gain-dbi", type=float)
    l.add_argument("--system-noise-temp-k", type=float)
    l.add_argument("--freq-mhz", type=float, required=True)
    l.add_argument("--distance-km", type=float)
    l.add_argument("--altitude-km", type=float)
    l.add_argument("--elevation-deg", type=float, default=10.0)
    l.add_argument("--atmospheric-loss-db", type=float,
                   help="no default: an absent atmosphere makes the margin Unknown")
    l.add_argument("--pointing-loss-db", type=float, default=0.0)
    l.add_argument("--data-rate-bps", type=float)
    l.add_argument("--modulation", help="BPSK QPSK 8PSK 16QAM 64QAM")
    l.add_argument("--target-ber", type=float, default=1e-5)
    l.add_argument("--coding-gain-db", type=float)
    l.add_argument("--required-ebn0-db", type=float)
    l.add_argument("--implementation-loss-db", type=float, default=2.0)
    l.set_defaults(fn=cmd_link)

    g = common(sub.add_parser("pass", help="orbit, Doppler, pass and beam dynamics"))
    g.add_argument("--altitude-km", type=float, required=True)
    g.add_argument("--freq-mhz", type=float, required=True)
    g.add_argument("--elevation-deg", type=float, default=10.0)
    g.add_argument("--beamwidth-deg", type=float)
    g.set_defaults(fn=cmd_pass)

    n = common(sub.add_parser("ntn", help="delay, HARQ, PRACH, duplex verdicts"))
    n.add_argument("--altitude-km", type=float, required=True)
    n.add_argument("--elevation-deg", type=float, default=10.0)
    n.add_argument("--architecture", default="regenerative",
                   choices=["regenerative", "bent_pipe", "bent-pipe"])
    n.add_argument("--feeder-link-km", type=float)
    n.add_argument("--numerology", type=int, default=1)
    n.add_argument("--harq-processes", type=int, default=16)
    n.add_argument("--preamble-format", default="format 0")
    n.add_argument("--cyclic-prefix-us", type=float, default=103.13)
    n.add_argument("--gnss", action="store_true", help="GNSS timing pre-compensation fitted")
    n.add_argument("--guard-period-us", type=float, default=71.35)
    n.set_defaults(fn=cmd_ntn)

    o = common(sub.add_parser("oran", help="functional split and feeder load"))
    o.add_argument("--split", default="option8",
                   choices=["option8", "option7-2x", "option2", "full-gnb"])
    o.add_argument("--sample-rate-msps", type=float)
    o.add_argument("--antenna-ports", type=int)
    o.add_argument("--bits-per-sample", type=int)
    o.add_argument("--used-subcarriers", type=int)
    o.add_argument("--symbols-per-second", type=float)
    o.add_argument("--user-throughput-bps", type=float)
    o.add_argument("--feeder-capacity-bps", type=float)
    o.set_defaults(fn=cmd_oran)

    h = common(sub.add_parser("hal", help="radios: census, spec, coverage"))
    h.add_argument("--device")
    h.add_argument("--freq-mhz", type=float)
    h.set_defaults(fn=cmd_hal)

    s = common(sub.add_parser("sota", help="state-of-the-art tracks and their rung"))
    s.add_argument("--track")
    s.add_argument("--promote")
    s.add_argument("--to", default="MODEL")
    s.add_argument("--evidence")
    s.set_defaults(fn=cmd_sota)

    b = common(sub.add_parser("bom", help="price a bill of materials online"))
    b.add_argument("file", nargs="?", default="bom/ground-station-sdr.csv")
    b.add_argument("--providers", help="comma-separated order, e.g. local,nexar,mouser")
    b.add_argument("--price-book", default="bom/prices.csv")
    b.add_argument("--currency")
    b.add_argument("--fx", help="declared exchange-rate file with source and date")
    b.add_argument("--cache", default="bom/.price-cache.json")
    b.add_argument("--cache-ttl-s", type=int, default=86400)
    b.add_argument("--no-cache", action="store_true")
    b.add_argument("--status", action="store_true", help="which providers are configured")
    b.add_argument("--out-md")
    b.add_argument("--out-csv")
    b.set_defaults(fn=cmd_bom)

    d = common(sub.add_parser("dispatch", help="emit the work packets"))
    d.add_argument("--out")
    d.set_defaults(fn=cmd_dispatch)

    dr = common(sub.add_parser("doctor", help="what is present, what is declared absent"))
    dr.set_defaults(fn=cmd_doctor)
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        return a.fn(a)
    except BrokenPipeError:          # piping into head is not an error
        try:
            sys.stdout.close()
        except Exception:
            pass
        return 0


if __name__ == "__main__":
    sys.exit(main())
