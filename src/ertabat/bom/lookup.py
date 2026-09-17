"""Price lookup: cache, provider order, and a result that carries its provenance.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import json
import os
import time

from .. import Unknown
from .model import PricedLine, PriceQuote, totals
from .providers import DEFAULT_ORDER, REGISTRY, LocalPriceBook


class Cache:
    """A JSON cache beside the BoM — never in /tmp, never outside the tree."""

    def __init__(self, path="bom/.price-cache.json", ttl_s=86400):
        self.path, self.ttl = path, ttl_s
        self._d = {}
        if os.path.exists(path):
            try:
                with open(path) as fh:
                    self._d = json.load(fh)
            except Exception:
                self._d = {}

    def get(self, key):
        e = self._d.get(key)
        if not e:
            return None
        if self.ttl and (time.time() - e.get("_t", 0)) > self.ttl:
            return None
        q = dict(e)
        q.pop("_t", None)
        return PriceQuote(**q)

    def put(self, key, quote: PriceQuote):
        d = quote.as_dict()
        d["_t"] = time.time()
        self._d[key] = d

    def flush(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w") as fh:
            json.dump(self._d, fh, indent=1, sort_keys=True)


class PriceService:
    def __init__(self, order=DEFAULT_ORDER, fetch=None, cache: Cache = None,
                 price_book=None, currency=None):
        self.order = tuple(order)
        self.cache = cache if cache is not None else Cache()
        self.currency = currency
        self.providers = []
        for k in self.order:
            cls = REGISTRY.get(k)
            if not cls:
                continue
            self.providers.append(LocalPriceBook(path=price_book)
                                  if cls is LocalPriceBook else
                                  (cls(fetch=fetch) if fetch else cls()))

    def status(self):
        return [{"provider": p.key, "display": p.display,
                 "available": bool(p.available()),
                 "reason": None if p.available() else str(p.why_unavailable())}
                for p in self.providers]

    def quote(self, mpn, qty=1, manufacturer="", use_cache=True):
        ck = f"{manufacturer.lower()}|{mpn.upper()}|{qty}|{self.currency or '*'}"
        if use_cache:
            hit = self.cache.get(ck)
            if hit:
                return hit
        reasons = []
        for p in self.providers:
            if not p.available():
                reasons.append(f"{p.key}: {p.why_unavailable().reason}")
                continue
            q = p.quote(mpn, qty=qty, currency=self.currency, manufacturer=manufacturer)
            if isinstance(q, PriceQuote):
                self.cache.put(ck, q)
                return q
            reasons.append(f"{p.key}: {q.reason}")
        return Unknown(f"no price for {mpn}", tuple(reasons))

    def price_bom(self, lines, use_cache=True, fx=None):
        priced = [PricedLine(l, self.quote(l.mpn, l.qty, l.manufacturer, use_cache))
                  for l in lines]
        self.cache.flush()
        return priced, totals(priced, fx=fx)


def load_fx(path):
    """{"base":"INR","date":"...","source":"...","rates":{"USD":88.1}} — no default."""
    if not path or not os.path.exists(path):
        return None
    with open(path) as fh:
        d = json.load(fh)
    for f in ("base", "rates", "source", "date"):
        if f not in d:
            raise ValueError(f"fx file needs '{f}' — an undated rate from an "
                             f"unnamed source is not a declaration")
    return d
