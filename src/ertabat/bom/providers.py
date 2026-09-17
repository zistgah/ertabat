"""Price providers. Keys live in files, never in flags; absence is declared.

Every provider is one class with the same three methods, so a new distributor is
an addition and never an edit (skills/agents/provider-authoring.md). The HTTP
call is injected, which is why the suite can prove the failure paths without a
network: a 403, an empty result and a malformed body must each end as Unknown
with a reason, and never as a number.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

from .. import Unknown
from .model import PriceQuote

TIMEOUT_S = 20


def _utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def http_json(url, *, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return Unknown(f"HTTP {e.code} from {url.split('?')[0]}",
                       ("credentials or quota",))
    except Exception as e:
        return Unknown(f"transport failure: {e.__class__.__name__}: {e}",
                       (url.split("?")[0],))


def read_key(path_env: str, literal_env: str = None):
    """Token by path. A literal in the environment is accepted but reported."""
    p = os.environ.get(path_env)
    if p and os.path.exists(os.path.expanduser(p)):
        with open(os.path.expanduser(p)) as fh:
            return fh.read().strip()
    if literal_env and os.environ.get(literal_env):
        return os.environ[literal_env].strip()
    return None


class PriceProvider:
    key = "provider"
    display = "provider"
    needs_key = True
    key_env = ""
    currency_hint = ""

    def __init__(self, fetch=http_json):
        self.fetch = fetch

    def available(self):
        if not self.needs_key:
            return True
        return read_key(self.key_env) is not None

    def why_unavailable(self):
        return Unknown(f"{self.display} not configured",
                       (f"{self.key_env}=<path to token file>",))

    def quote(self, mpn, qty=1, currency=None, manufacturer=""):
        raise NotImplementedError


class LocalPriceBook(PriceProvider):
    """The keyless path. A CSV or JSON price book, priced by hand or by quote.

    Distributor APIs all want an account. This provider exists so the tool is
    fully usable with none of them: paste the quotations you already have.
    Format: mpn,unit_price,currency,qty_break,source,retrieved_utc[,url]
    """
    key = "local"
    display = "local price book"
    needs_key = False

    def __init__(self, path=None, rows=None, fetch=None):
        super().__init__(fetch or (lambda *a, **k: None))
        self.path = path
        self._rows = rows

    def _load(self):
        if self._rows is not None:
            return self._rows
        if not self.path or not os.path.exists(self.path):
            return []
        with open(self.path) as fh:
            txt = fh.read()
        if self.path.endswith(".json"):
            return json.loads(txt)
        import csv as _csv
        import io as _io
        return list(_csv.DictReader(_io.StringIO(txt)))

    def available(self):
        return bool(self._load())

    def why_unavailable(self):
        return Unknown("no local price book",
                       ("bom/prices.csv", "mpn,unit_price,currency,qty_break,source,retrieved_utc"))

    def quote(self, mpn, qty=1, currency=None, manufacturer=""):
        for r in self._load():
            if (r.get("mpn") or "").strip().upper() != mpn.strip().upper():
                continue
            if currency and (r.get("currency") or "").upper() != currency.upper():
                continue
            if not r.get("retrieved_utc") or not r.get("source"):
                return Unknown(f"{mpn}: price book row carries no source or date",
                               ("source", "retrieved_utc"))
            return PriceQuote(mpn, float(r["unit_price"]), (r.get("currency") or "").upper(),
                              int(r.get("qty_break") or 1), f"local:{r['source']}",
                              r["retrieved_utc"], r.get("url", ""),
                              note="declared by hand, not fetched")
        return Unknown(f"{mpn} is not in the local price book", ("add the row",))


class NexarProvider(PriceProvider):
    """Octopart via the Nexar GraphQL API. Aggregates most distributors."""
    key = "nexar"
    display = "Nexar / Octopart"
    key_env = "ERTABAT_NEXAR_TOKEN_FILE"
    endpoint = "https://api.nexar.com/graphql"
    QUERY = ("query($q:String!,$n:Int!){supSearchMpn(q:$q,limit:$n)"
             "{results{part{mpn manufacturer{name} sellers{company{name} "
             "offers{clickUrl inventoryLevel prices{quantity price currency}}}}}}}")

    def quote(self, mpn, qty=1, currency=None, manufacturer=""):
        tok = read_key(self.key_env)
        if not tok:
            return self.why_unavailable()
        body = json.dumps({"query": self.QUERY, "variables": {"q": mpn, "n": 1}}).encode()
        d = self.fetch(self.endpoint, data=body, method="POST", headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {tok}"})
        if isinstance(d, Unknown):
            return d
        try:
            res = d["data"]["supSearchMpn"]["results"]
            if not res:
                return Unknown(f"{mpn}: no result from {self.display}")
            best = None
            for s in res[0]["part"]["sellers"]:
                for off in s["offers"]:
                    for p in off["prices"]:
                        if p["quantity"] <= qty and (currency is None or
                                                     p["currency"].upper() == currency.upper()):
                            cand = (p["price"], p["currency"].upper(), p["quantity"],
                                    s["company"]["name"], off.get("clickUrl", ""),
                                    off.get("inventoryLevel"))
                            if best is None or cand[0] < best[0]:
                                best = cand
            if best is None:
                return Unknown(f"{mpn}: offers exist but none at qty {qty}"
                               + (f" in {currency}" if currency else ""))
            return PriceQuote(mpn, float(best[0]), best[1], best[2],
                              f"nexar:{best[3]}", _utc(), best[4], best[5])
        except (KeyError, TypeError, IndexError) as e:
            return Unknown(f"{self.display} response did not match the expected "
                           f"shape ({e.__class__.__name__}) — the schema moved")


class MouserProvider(PriceProvider):
    key = "mouser"
    display = "Mouser"
    key_env = "ERTABAT_MOUSER_KEY_FILE"
    endpoint = "https://api.mouser.com/api/v1/search/partnumber"

    def quote(self, mpn, qty=1, currency=None, manufacturer=""):
        k = read_key(self.key_env)
        if not k:
            return self.why_unavailable()
        body = json.dumps({"SearchByPartRequest": {"mouserPartNumber": mpn}}).encode()
        d = self.fetch(f"{self.endpoint}?apiKey={k}", data=body, method="POST",
                       headers={"Content-Type": "application/json"})
        if isinstance(d, Unknown):
            return d
        try:
            parts = d["SearchResults"]["Parts"]
            if not parts:
                return Unknown(f"{mpn}: no result from {self.display}")
            p = parts[0]
            best = None
            for br in p.get("PriceBreaks", []):
                q = int(br["Quantity"])
                if q <= qty:
                    val = float(str(br["Price"]).replace("$", "").replace(",", "").strip())
                    if best is None or q > best[2]:
                        best = (val, br.get("Currency", "USD").upper(), q)
            if best is None:
                return Unknown(f"{mpn}: {self.display} lists no break at or below qty {qty}")
            return PriceQuote(mpn, best[0], best[1], best[2], "mouser", _utc(),
                              p.get("ProductDetailUrl", ""), p.get("Availability"))
        except (KeyError, TypeError, ValueError) as e:
            return Unknown(f"{self.display} response unparseable: {e.__class__.__name__}")


class Element14Provider(PriceProvider):
    """Farnell / element14 — the one with an India storefront and INR prices."""
    key = "element14"
    display = "element14 / Farnell"
    key_env = "ERTABAT_ELEMENT14_KEY_FILE"
    endpoint = "https://api.element14.com/catalog/products"
    store = os.environ.get("ERTABAT_ELEMENT14_STORE", "in.element14.com")

    def quote(self, mpn, qty=1, currency=None, manufacturer=""):
        k = read_key(self.key_env)
        if not k:
            return self.why_unavailable()
        url = (f"{self.endpoint}?term=manuPartNum:{mpn}&storeInfo.id={self.store}"
               f"&resultsSettings.responseGroup=prices&callInfo.responseDataFormat=json"
               f"&callInfo.apiKey={k}")
        d = self.fetch(url)
        if isinstance(d, Unknown):
            return d
        try:
            prods = d["manufacturerPartNumberSearchReturn"]["products"]
            if not prods:
                return Unknown(f"{mpn}: no result from {self.display}")
            p = prods[0]
            best = None
            for br in p.get("prices", []):
                q = int(br["from"])
                if q <= qty and (best is None or q > best[2]):
                    best = (float(br["cost"]), "INR" if ".in." in self.store else "GBP", q)
            if best is None:
                return Unknown(f"{mpn}: {self.display} lists no break at or below qty {qty}")
            return PriceQuote(mpn, best[0], best[1], best[2], f"element14:{self.store}",
                              _utc(), "", p.get("inventoryCode"),
                              note="store currency inferred from the storefront")
        except (KeyError, TypeError, ValueError) as e:
            return Unknown(f"{self.display} response unparseable: {e.__class__.__name__}")


class DigiKeyProvider(PriceProvider):
    key = "digikey"
    display = "DigiKey"
    key_env = "ERTABAT_DIGIKEY_TOKEN_FILE"
    endpoint = "https://api.digikey.com/products/v4/search/keyword"

    def quote(self, mpn, qty=1, currency=None, manufacturer=""):
        tok = read_key(self.key_env)
        if not tok:
            return Unknown("DigiKey not configured — it also needs an OAuth2 "
                           "client credential exchange, not a static key",
                           (f"{self.key_env}=<path to bearer token>",
                            "ERTABAT_DIGIKEY_CLIENT_ID"))
        body = json.dumps({"Keywords": mpn, "Limit": 1}).encode()
        d = self.fetch(self.endpoint, data=body, method="POST", headers={
            "Authorization": f"Bearer {tok}", "Content-Type": "application/json",
            "X-DIGIKEY-Client-Id": os.environ.get("ERTABAT_DIGIKEY_CLIENT_ID", "")})
        if isinstance(d, Unknown):
            return d
        try:
            prods = d.get("Products") or []
            if not prods:
                return Unknown(f"{mpn}: no result from {self.display}")
            p = prods[0]
            var = (p.get("ProductVariations") or [{}])[0]
            best = None
            for br in var.get("StandardPricing", []):
                q = int(br["BreakQuantity"])
                if q <= qty and (best is None or q > best[2]):
                    best = (float(br["UnitPrice"]), "USD", q)
            if best is None:
                return Unknown(f"{mpn}: {self.display} lists no break at or below qty {qty}")
            return PriceQuote(mpn, best[0], best[1], best[2], "digikey", _utc(),
                              p.get("ProductUrl", ""), p.get("QuantityAvailable"))
        except (KeyError, TypeError, ValueError) as e:
            return Unknown(f"{self.display} response unparseable: {e.__class__.__name__}")


class LCSCProvider(PriceProvider):
    """Declared, not implemented: LCSC publishes no open catalogue API.

    Screen-scraping a storefront would work until it did not, and would put a
    silently stale number into a cost model. So this provider says so.
    """
    key = "lcsc"
    display = "LCSC"
    needs_key = False

    def available(self):
        return False

    def why_unavailable(self):
        return Unknown("LCSC has no public catalogue API carried here",
                       ("export a cart to the local price book",))

    def quote(self, mpn, qty=1, currency=None, manufacturer=""):
        return self.why_unavailable()


REGISTRY = {c.key: c for c in (LocalPriceBook, NexarProvider, MouserProvider,
                               Element14Provider, DigiKeyProvider, LCSCProvider)}
DEFAULT_ORDER = ("local", "nexar", "mouser", "element14", "digikey", "lcsc")
