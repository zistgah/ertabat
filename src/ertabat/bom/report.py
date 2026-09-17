"""BoM report: every line says where its number came from, or that it has none.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import csv
import io

from .. import Unknown


def to_markdown(priced, tot, title="Bill of materials"):
    o = [f"# {title}", ""]
    o.append(f"{tot['lines_priced']} of {tot['lines_total']} lines priced.")
    o.append("")
    o.append("| ref | mpn | qty | unit | ccy | extended | source | retrieved |")
    o.append("|---|---|---:|---:|---|---:|---|---|")
    for pl in priced:
        l = pl.line
        if pl.priced:
            q = pl.quote
            o.append(f"| {l.ref} | {l.mpn} | {l.qty} | {q.unit_price:.4f} | "
                     f"{q.currency} | {pl.extended:.2f} | {q.source} | {q.retrieved_utc} |")
        else:
            o.append(f"| {l.ref} | {l.mpn} | {l.qty} | — | — | — | "
                     f"no price | — |")
    o.append("")
    for c, v in tot["per_currency"].items():
        o.append(f"- subtotal {c}: {v:,.2f}")
    comb = tot.get("combined")
    if isinstance(comb, Unknown):
        o.append(f"- **total: {comb}**")
    elif comb:
        o.append(f"- **total: {comb['value']:,.2f} {comb['currency']}** "
                 f"(rates: {comb['fx']})")
    if tot["lines_unpriced"]:
        o.append("")
        o.append("## Unpriced")
        for pl in priced:
            if not pl.priced:
                o.append(f"- `{pl.line.ref}` {pl.line.mpn} — {pl.quote}")
    return "\n".join(o) + "\n"


def to_csv(priced):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ref", "mpn", "manufacturer", "qty", "unit_price", "currency",
                "qty_break", "extended", "source", "retrieved_utc", "url", "status"])
    for pl in priced:
        l = pl.line
        if pl.priced:
            q = pl.quote
            w.writerow([l.ref, l.mpn, l.manufacturer, l.qty, f"{q.unit_price:.6f}",
                        q.currency, q.qty_break, f"{pl.extended:.6f}", q.source,
                        q.retrieved_utc, q.url, "priced"])
        else:
            w.writerow([l.ref, l.mpn, l.manufacturer, l.qty, "", "", "", "", "", "",
                        "", f"UNPRICED: {pl.quote.reason}"])
    return buf.getvalue()
