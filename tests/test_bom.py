"""BoM pricing: every failure path ends as Unknown, never as a number.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
import json
import os
import tempfile
import unittest

from ertabat import Unknown
from ertabat.bom.lookup import Cache, PriceService, load_fx
from ertabat.bom.model import BomLine, PriceQuote, parse_csv, totals
from ertabat.bom.providers import (Element14Provider, LocalPriceBook, MouserProvider,
                                NexarProvider, read_key)
from ertabat.bom.report import to_csv, to_markdown

NEXAR_OK = {"data": {"supSearchMpn": {"results": [{"part": {
    "mpn": "X1", "manufacturer": {"name": "Acme"}, "sellers": [
        {"company": {"name": "Distributor A"}, "offers": [
            {"clickUrl": "https://example.invalid/x1", "inventoryLevel": 42,
             "prices": [{"quantity": 1, "price": 12.5, "currency": "USD"},
                        {"quantity": 10, "price": 9.75, "currency": "USD"}]}]}]}}]}}}


def fetch_returning(payload, counter=None):
    def _f(url, **kw):
        if counter is not None:
            counter.append(url)
        return payload
    return _f


class TestProviderFailurePaths(unittest.TestCase):
    """A price is a number. Everything that is not a number must be Unknown."""

    def setUp(self):
        os.environ["ERTABAT_NEXAR_TOKEN_FILE"] = self._tokfile()

    def _tokfile(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "tok")
        open(p, "w").write("test-token")
        return p

    def tearDown(self):
        os.environ.pop("ERTABAT_NEXAR_TOKEN_FILE", None)

    def test_http_403_is_unknown_not_zero(self):
        p = NexarProvider(fetch=fetch_returning(Unknown("HTTP 403 from api", ("credentials",))))
        q = p.quote("X1", 1)
        self.assertIsInstance(q, Unknown)
        self.assertIn("403", q.reason)

    def test_empty_result_is_unknown(self):
        p = NexarProvider(fetch=fetch_returning({"data": {"supSearchMpn": {"results": []}}}))
        self.assertIsInstance(p.quote("X1", 1), Unknown)

    def test_malformed_body_is_unknown_and_says_the_schema_moved(self):
        p = NexarProvider(fetch=fetch_returning({"unexpected": True}))
        q = p.quote("X1", 1)
        self.assertIsInstance(q, Unknown)
        self.assertIn("schema", q.reason)

    def test_a_good_body_gives_the_right_break(self):
        p = NexarProvider(fetch=fetch_returning(NEXAR_OK))
        q = p.quote("X1", 10)
        self.assertIsInstance(q, PriceQuote)
        self.assertEqual(q.unit_price, 9.75)
        self.assertEqual(q.qty_break, 10)
        self.assertEqual(q.currency, "USD")
        self.assertTrue(q.retrieved_utc.endswith("Z"))

    def test_qty_below_every_break_is_unknown(self):
        body = json.loads(json.dumps(NEXAR_OK))
        body["data"]["supSearchMpn"]["results"][0]["part"]["sellers"][0]["offers"][0]["prices"] = [
            {"quantity": 100, "price": 1.0, "currency": "USD"}]
        p = NexarProvider(fetch=fetch_returning(body))
        self.assertIsInstance(p.quote("X1", 1), Unknown)

    def test_missing_key_is_declared_never_skipped_silently(self):
        os.environ.pop("ERTABAT_NEXAR_TOKEN_FILE", None)
        p = NexarProvider(fetch=fetch_returning(NEXAR_OK))
        self.assertFalse(p.available())
        q = p.quote("X1", 1)
        self.assertIsInstance(q, Unknown)
        self.assertIn("ERTABAT_NEXAR_TOKEN_FILE", " ".join(q.needs))

    def test_key_is_read_from_a_file_not_a_flag(self):
        p = self._tokfile()
        os.environ["ERTABAT_MOUSER_KEY_FILE"] = p
        self.assertEqual(read_key("ERTABAT_MOUSER_KEY_FILE"), "test-token")
        os.environ.pop("ERTABAT_MOUSER_KEY_FILE")


class TestLocalPriceBook(unittest.TestCase):
    def test_row_without_provenance_is_refused(self):
        b = LocalPriceBook(rows=[{"mpn": "X1", "unit_price": "10", "currency": "INR"}])
        q = b.quote("X1")
        self.assertIsInstance(q, Unknown)
        self.assertIn("source", " ".join(q.needs))

    def test_good_row_prices(self):
        b = LocalPriceBook(rows=[{"mpn": "X1", "unit_price": "10", "currency": "INR",
                                  "qty_break": "1", "source": "quotation",
                                  "retrieved_utc": "2026-09-15T00:00:00Z"}])
        q = b.quote("X1")
        self.assertEqual(q.unit_price, 10.0)
        self.assertIn("local:", q.source)


class TestTotals(unittest.TestCase):
    def _pl(self, ccy, val, ref="A"):
        from ertabat.bom.model import PricedLine
        return PricedLine(BomLine(ref, "X" + ref, 1),
                          PriceQuote("X" + ref, val, ccy, 1, "test", "2026-09-15T00:00:00Z"))

    def _unpriced(self, ref="Z"):
        from ertabat.bom.model import PricedLine
        return PricedLine(BomLine(ref, "X" + ref, 1), Unknown("no price"))

    def test_single_currency_totals(self):
        t = totals([self._pl("INR", 100), self._pl("INR", 50, "B")])
        self.assertEqual(t["combined"]["value"], 150.0)

    def test_mixed_currency_without_declared_rates_is_unknown(self):
        t = totals([self._pl("INR", 100), self._pl("USD", 50, "B")])
        self.assertIsInstance(t["combined"], Unknown)
        self.assertIn("exchange rate", t["combined"].reason)

    def test_mixed_currency_with_declared_rates_totals(self):
        fx = {"base": "INR", "rates": {"USD": 88.0}, "source": "declared", "date": "2026-09-15"}
        t = totals([self._pl("INR", 100), self._pl("USD", 50, "B")], fx=fx)
        self.assertEqual(t["combined"]["value"], 100 + 50 * 88.0)

    def test_an_unpriced_line_blocks_the_total(self):
        t = totals([self._pl("INR", 100), self._unpriced()])
        self.assertIsInstance(t["combined"], Unknown)
        self.assertEqual(t["lines_priced"], 1)
        self.assertEqual(t["unpriced_refs"], ["Z"])

    def test_subtotal_still_shown_so_partial_is_visible(self):
        t = totals([self._pl("INR", 100), self._unpriced()])
        self.assertEqual(t["per_currency"]["INR"], 100.0)

    def test_fx_file_without_a_date_is_refused(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "fx.json")
        json.dump({"base": "INR", "rates": {"USD": 88.0}}, open(p, "w"))
        with self.assertRaises(ValueError):
            load_fx(p)


class TestService(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.cache = os.path.join(self.d, "cache.json")
        self.book = os.path.join(self.d, "prices.csv")
        open(self.book, "w").write(
            "mpn,unit_price,currency,qty_break,source,retrieved_utc\n"
            "X1,100,INR,1,quotation,2026-09-15T00:00:00Z\n")

    def test_cache_prevents_a_second_call(self):
        calls = []
        os.environ["ERTABAT_NEXAR_TOKEN_FILE"] = self.book  # any existing file
        svc = PriceService(order=("nexar",), fetch=fetch_returning(NEXAR_OK, calls),
                           cache=Cache(path=self.cache))
        svc.quote("X1", 1)
        n = len(calls)
        svc.quote("X1", 1)
        self.assertEqual(len(calls), n, "second lookup went back to the network")
        os.environ.pop("ERTABAT_NEXAR_TOKEN_FILE")

    def test_provider_order_is_honoured_and_reasons_accumulate(self):
        svc = PriceService(order=("local", "lcsc"), price_book=self.book,
                           cache=Cache(path=self.cache))
        self.assertIsInstance(svc.quote("X1"), PriceQuote)
        q = svc.quote("NOT-A-PART")
        self.assertIsInstance(q, Unknown)
        self.assertTrue(any("lcsc" in n for n in q.needs))
        self.assertTrue(any("local" in n for n in q.needs))

    def test_status_names_what_is_missing(self):
        svc = PriceService(cache=Cache(path=self.cache))
        st = {s["provider"]: s for s in svc.status()}
        self.assertIn("nexar", st)
        self.assertFalse(st["nexar"]["available"])
        self.assertIn("ERTABAT_NEXAR_TOKEN_FILE", st["nexar"]["reason"])

    def test_end_to_end_report_marks_unpriced_lines(self):
        lines = parse_csv("ref,mpn,qty\nA1,X1,1\nA2,X2,2\n")
        svc = PriceService(order=("local",), price_book=self.book,
                           cache=Cache(path=self.cache))
        priced, tot = svc.price_bom(lines)
        md = to_markdown(priced, tot)
        self.assertIn("1 of 2 lines priced", md)
        self.assertIn("## Unpriced", md)
        self.assertIn("UNPRICED", to_csv(priced))
        self.assertNotIn("| A2 | X2 | 2 | 0", md)

    def test_bom_without_a_part_number_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_csv("ref,mpn,qty\nA1,,1\n")


if __name__ == "__main__":
    unittest.main()
