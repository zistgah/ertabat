"""Link budget and modulation: the arithmetic, and the refusal to guess.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
import math
import unittest

from ertabat import Unknown, known
from ertabat.link.budget import fspl_db, link_budget, slant_range_km, g_over_t_db
from ertabat.link import modulation as mod


class TestBudget(unittest.TestCase):
    def test_fspl_matches_closed_form(self):
        self.assertAlmostEqual(fspl_db(550, 437), 140.065, places=2)
        self.assertAlmostEqual(fspl_db(36000, 12000), 205.157, places=2)

    def test_slant_range_geometry(self):
        self.assertAlmostEqual(slant_range_km(550, 90), 550.0, places=6)
        self.assertAlmostEqual(slant_range_km(550, 10), 1815.65, places=1)
        self.assertGreater(slant_range_km(550, 5), slant_range_km(550, 10))

    def test_absent_atmosphere_poisons_the_margin(self):
        """The gate that matters: a budget with no atmosphere must not close."""
        r = link_budget(tx_power_dbw=0, tx_gain_dbi=2, distance_km=550, freq_mhz=437,
                        rx_gain_dbi=18, system_noise_temp_k=250,
                        data_rate_bps=9600, required_eb_over_n0_db=9.6)
        self.assertIsInstance(r.margin_db, Unknown)
        self.assertFalse(r.closes())

    def test_unknown_refuses_arithmetic(self):
        with self.assertRaises(TypeError):
            Unknown("no value") + 1.0

    def test_margin_arithmetic(self):
        r = link_budget(tx_power_dbw=0, tx_gain_dbi=2, distance_km=550, freq_mhz=437,
                        atmospheric_loss_db=1.0, rx_gain_dbi=18,
                        system_noise_temp_k=250, data_rate_bps=9600,
                        required_eb_over_n0_db=9.6, implementation_loss_db=2.0)
        expect = (2.0 - fspl_db(550, 437) - 1.0 + g_over_t_db(18, 250) + 228.6
                  - 10 * math.log10(9600) - 9.6 - 2.0)
        self.assertAlmostEqual(r.margin_db, expect, places=6)

    def test_missing_rate_leaves_ebn0_unknown(self):
        r = link_budget(tx_power_dbw=0, tx_gain_dbi=2, distance_km=550, freq_mhz=437,
                        atmospheric_loss_db=1.0, rx_gain_dbi=18, system_noise_temp_k=250)
        self.assertIsInstance(r.eb_over_n0_db, Unknown)
        self.assertIn("data_rate_bps", r.eb_over_n0_db.needs)


class TestModulation(unittest.TestCase):
    def test_required_ebn0_is_derived_not_recalled(self):
        """Inverting Q() must land on the textbook figures, to 0.1 dB."""
        for scheme, expect in (("BPSK", 9.59), ("QPSK", 9.59), ("8PSK", 12.97),
                               ("16QAM", 13.43)):
            self.assertAlmostEqual(mod.required_ebn0_db(scheme, 1e-5), expect, delta=0.1)

    def test_ber_is_monotonic(self):
        prev = 1.0
        for db in range(0, 14):
            b = mod.ber_awgn("QPSK", db)
            self.assertLess(b, prev)
            prev = b

    def test_coding_gain_must_be_declared(self):
        self.assertIsInstance(mod.spectral_efficiency("16QAM", None), Unknown)
        self.assertAlmostEqual(mod.spectral_efficiency("16QAM", 0.5), 2.0)

    def test_unknown_scheme_declares(self):
        self.assertIsInstance(mod.required_ebn0_db("GFSK-SOMETHING"), Unknown)


if __name__ == "__main__":
    unittest.main()
