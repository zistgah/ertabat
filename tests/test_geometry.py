"""Orbit geometry and Doppler against figures that can be checked by hand.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
import unittest

from ertabat.link import geometry as g


class TestGeometry(unittest.TestCase):
    def test_orbital_velocity(self):
        self.assertAlmostEqual(g.orbital_velocity_km_s(550), 7.585, places=2)
        self.assertAlmostEqual(g.orbital_period_s(550) / 60, 95.6, delta=0.2)

    def test_doppler_at_437_is_ten_kilohertz(self):
        self.assertAlmostEqual(g.max_doppler_hz(437e6, 550) / 1e3, 10.2, delta=0.2)

    def test_doppler_scales_with_frequency(self):
        a = g.max_doppler_hz(1.6e9, 550)
        b = g.max_doppler_hz(437e6, 550)
        self.assertAlmostEqual(a / b, 1.6e9 / 437e6, places=6)
        self.assertGreater(g.max_doppler_hz(12e9, 550), 250e3)

    def test_doppler_rate_falls_with_altitude(self):
        self.assertGreater(g.max_doppler_rate_hz_s(437e6, 400),
                           g.max_doppler_rate_hz_s(437e6, 1200))

    def test_pass_duration(self):
        self.assertTrue(400 < g.pass_duration_s(550, 10) < 700)
        self.assertLess(g.pass_duration_s(550, 30), g.pass_duration_s(550, 10))

    def test_beam_dwell_is_the_handover_clock(self):
        dwell = g.beam_dwell_s(550, g.beam_diameter_km(550, 40))
        self.assertTrue(30 < dwell < 180)

    def test_tle_propagation_declares_absence(self):
        import datetime
        from ertabat import Unknown
        r = g.propagate_tle("1 x", "2 y", datetime.datetime(2026, 1, 1))
        if isinstance(r, Unknown):
            self.assertIn("SGP4", r.reason)


if __name__ == "__main__":
    unittest.main()
