"""Bill of materials: lines, quotes, and totals that refuse to round up to a lie.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field, asdict

from .. import Unknown


@dataclass
class BomLine:
    ref: str
    mpn: str
    qty: int = 1
    manufacturer: str = ""
    description: str = ""
    alternates: tuple = field(default_factory=tuple)
    subsystem: str = ""

    def key(self):
        return (self.manufacturer.strip().lower(), self.mpn.strip().upper())


@dataclass(frozen=True)
class PriceQuote:
    mpn: str
    unit_price: float
    currency: str
    qty_break: int
    source: str
    retrieved_utc: str
    url: str = ""
    stock: object = None
    note: str = ""

    def extended(self, qty: int) -> float:
        return self.unit_price * qty

    def as_dict(self):
        return asdict(self)


def parse_csv(text: str):
    """ref,mpn,qty,manufacturer,description,subsystem — header required."""
    rows, out = list(csv.DictReader(io.StringIO(text))), []
    for i, r in enumerate(rows, 2):
        if not (r.get("mpn") or "").strip():
            raise ValueError(f"line {i}: mpn is empty — a BoM line without a "
                             f"part number cannot be priced or ordered")
        out.append(BomLine(
            ref=(r.get("ref") or f"L{i-1}").strip(),
            mpn=r["mpn"].strip(),
            qty=int((r.get("qty") or "1").strip() or 1),
            manufacturer=(r.get("manufacturer") or "").strip(),
            description=(r.get("description") or "").strip(),
            subsystem=(r.get("subsystem") or "").strip(),
            alternates=tuple(a.strip() for a in (r.get("alternates") or "").split("|") if a.strip()),
        ))
    return out


@dataclass
class PricedLine:
    line: BomLine
    quote: object          # PriceQuote or Unknown

    @property
    def priced(self) -> bool:
        return isinstance(self.quote, PriceQuote)

    @property
    def extended(self):
        return self.quote.extended(self.line.qty) if self.priced else self.quote


def totals(priced_lines, fx=None):
    """Per-currency totals, plus a single total ONLY if the rates are declared.

    A BoM half-priced in USD and half in INR has no single number until someone
    says which rate, on which date, from which source. `fx` is that declaration
    or the combined total stays Unknown.
    """
    per = {}
    unknown = []
    for pl in priced_lines:
        if pl.priced:
            per[pl.quote.currency] = per.get(pl.quote.currency, 0.0) + pl.extended
        else:
            unknown.append(pl.line.ref)
    out = {
        "per_currency": {k: round(v, 4) for k, v in sorted(per.items())},
        "lines_total": len(priced_lines),
        "lines_priced": len(priced_lines) - len(unknown),
        "lines_unpriced": len(unknown),
        "unpriced_refs": unknown,
    }
    if unknown:
        out["combined"] = Unknown(
            f"{len(unknown)} of {len(priced_lines)} lines have no price — "
            "a total over the priced subset would read as the cost of the build",
            tuple(unknown[:12]))
        return out
    if len(per) == 1:
        c, v = next(iter(per.items()))
        out["combined"] = {"value": round(v, 4), "currency": c, "fx": "not needed"}
        return out
    if not fx:
        out["combined"] = Unknown(
            f"lines are quoted in {', '.join(sorted(per))} and no exchange rate "
            "has been declared", ("--fx <file>", "rate source", "rate date"))
        return out
    miss = [c for c in per if c != fx.get("base") and c not in fx.get("rates", {})]
    if miss:
        out["combined"] = Unknown(f"no declared rate for {', '.join(miss)}",
                                  tuple(miss))
        return out
    tot = 0.0
    for c, v in per.items():
        tot += v if c == fx["base"] else v * fx["rates"][c]
    out["combined"] = {"value": round(tot, 4), "currency": fx["base"],
                       "fx": f"{fx.get('source','declared')} @ {fx.get('date','undated')}"}
    return out
