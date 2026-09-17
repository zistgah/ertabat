"""The atmosphere module must declare what it does not know.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
import json
import os
import unittest

from ertabat import Unknown
from ertabat.link import atmosphere as atm

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
P838 = os.path.join(DATA, "itu_p838.json")
P676 = os.path.join(DATA, "itu_p676.json")


def _rows(path):
    if not os.path.exists(path):
        return False
    try:
        with open(path) as fh:
            return bool(json.load(fh).get("rows"))
    except Exception:
        return False


class TestDeclaresRatherThanGuesses(unittest.TestCase):
    """These run always. They are the reason the tables may ship empty."""

    def test_rain_declares_when_the_table_is_absent_or_empty(self):
        if _rows(P838):
            self.skipTest("table populated — see the populated tests below")
        r = atm.specific_rain_attenuation_db_km(12, 30, "horizontal")
        self.assertIsInstance(r, Unknown)
        self.assertIn("P.838", r.reason)

    def test_total_refuses_to_sum_around_a_hole(self):
        t = atm.total_atmospheric_loss_db(freq_ghz=12, elevation_deg=30,
                                          rain_rate_mm_h=30)
        self.assertIsInstance(t, Unknown)

    def test_ionospheric_scintillation_is_declared_not_modelled(self):
        self.assertIsInstance(atm.ionospheric_scintillation_index(1.6, 10, 20), Unknown)

    def test_a_table_without_provenance_is_not_a_table(self):
        import tempfile
        d = tempfile.mkdtemp()
        p = os.path.join(d, "itu_p838.json")
        with open(p, "w") as fh:
            json.dump({"rows": [[12, 0.02, 1.1, 0.02, 1.1]]}, fh)
        old = atm._DATA
        try:
            atm._DATA = d
            r = atm.specific_rain_attenuation_db_km(12, 30, "horizontal")
            self.assertIsInstance(r, Unknown)
            self.assertIn("provenance", r.reason)
        finally:
            atm._DATA = old


@unittest.skipUnless(_rows(P838),
                     "packet ATM-1 not delivered: data/itu_p838.json is empty")
class TestPopulated(unittest.TestCase):
    """These start running the moment packet ATM-1 lands."""

    def test_populated_rain_gives_a_number(self):
        g = atm.specific_rain_attenuation_db_km(12, 30, "horizontal")
        self.assertNotIsInstance(g, Unknown)
        self.assertGreater(g, 0)

    def test_attenuation_rises_with_rain_rate(self):
        a = atm.specific_rain_attenuation_db_km(12, 10, "horizontal")
        b = atm.specific_rain_attenuation_db_km(12, 50, "horizontal")
        self.assertGreater(b, a)

    def test_ku_is_worse_than_l_band(self):
        l = atm.specific_rain_attenuation_db_km(1.5, 30, "horizontal")
        ku = atm.specific_rain_attenuation_db_km(12, 30, "horizontal")
        self.assertGreater(ku, l)

    def test_extrapolation_is_refused(self):
        self.assertIsInstance(
            atm.specific_rain_attenuation_db_km(400, 30, "horizontal"), Unknown)


class TestGaseous(unittest.TestCase):
    def test_gaseous_declares_when_absent(self):
        if _rows(P676):
            self.skipTest("packet ATM-2 delivered")
        self.assertIsInstance(atm.gaseous_absorption_db(12, 30, 7.5), Unknown)


class TestScintillation(unittest.TestCase):
    def test_scintillation_needs_nwet_and_says_so(self):
        r = atm.scintillation_fade_db(12, 10, 0.6)
        self.assertIsInstance(r, Unknown)
        self.assertIn("n_wet", " ".join(r.needs) + r.reason)


if __name__ == "__main__":
    unittest.main()
