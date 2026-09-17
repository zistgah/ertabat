# Adding a distributor to the BoM pricer

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.

    class MyDistributor(PriceProvider):
        key = "mydist"
        display = "My Distributor"
        key_env = "ERTABAT_MYDIST_KEY_FILE"     # a PATH to a file, never the key
        endpoint = "https://api.example.com/v1/search"

        def quote(self, mpn, qty=1, currency=None, manufacturer=""):
            k = read_key(self.key_env)
            if not k:
                return self.why_unavailable()
            d = self.fetch(self.endpoint, data=..., headers=...)
            if isinstance(d, Unknown):
                return d                      # transport already declared it
            try:
                ...
                return PriceQuote(mpn, price, currency, break_qty,
                                  "mydist", _utc(), url, stock)
            except (KeyError, TypeError, ValueError) as e:
                return Unknown(f"{self.display} response unparseable: "
                               f"{e.__class__.__name__}")

Register it in `REGISTRY` and, if it should be consulted by default, in
`DEFAULT_ORDER`.

## The three tests your provider must pass

`self.fetch` is injected precisely so these need no network:

1. a 403 or any transport failure ends as `Unknown` mentioning credentials;
2. an empty result set ends as `Unknown`, not as a zero price;
3. a body that does not match the expected shape ends as `Unknown` saying the
   schema moved — an API changing under you is normal, and pretending otherwise
   is how a stale parser starts returning the wrong field as a price.

Copy the shape from `tests/test_bom.py::TestProviderFailurePaths`.

## Quantity breaks and currency

Return the break at or below the requested quantity, never above it. Carry the
currency the API returned; do not convert. Conversion happens once, against a
declared rate file, in `bom/model.totals`.
