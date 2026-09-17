"""Where terrestrial timing breaks in orbit — asserted, not asserted about.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
import unittest

from ertabat import Unknown
from ertabat.link.budget import slant_range_km
from ertabat.link.geometry import beam_diameter_km, beam_dwell_s
from ertabat.ntn import duplex, oran, timing


class TestTiming(unittest.TestCase):
    def setUp(self):
        self.far = slant_range_km(550, 10)
        self.near = slant_range_km(550, 90)
        self.b = timing.delay_budget(self.far, service_link_min_km=self.near)

    def test_rtt(self):
        self.assertAlmostEqual(self.b.one_way_ms, 6.06, delta=0.05)
        self.assertAlmostEqual(self.b.rtt_ms, 12.11, delta=0.1)

    def test_bent_pipe_doubles_the_loop(self):
        bp = timing.delay_budget(self.far, feeder_link_km=self.far,
                                 architecture="bent_pipe")
        self.assertAlmostEqual(bp.rtt_ms, 2 * self.b.rtt_ms, delta=0.01)

    def test_bent_pipe_without_feeder_declares(self):
        self.assertIsInstance(timing.delay_budget(self.far, architecture="bent_pipe"),
                              Unknown)

    def test_sixteen_harq_processes_are_not_enough(self):
        v = timing.harq_verdict(self.b.rtt_ms, timing.slot_duration_ms(1), 16)
        self.assertGreater(v["processes_needed"], 16)
        self.assertFalse(v["feasible_with_feedback"])
        self.assertIsNotNone(v["remedy"])

    def test_k_offset_covers_the_rtt(self):
        k = timing.k_offset_slots(self.b.rtt_ms, 1)
        self.assertGreaterEqual(k * timing.slot_duration_ms(1), self.b.rtt_ms)

    def test_prach_fails_without_precompensation_and_passes_with_it(self):
        bad = timing.prach_verdict(self.b.differential_ms, "format 0", 103.13,
                                   gnss_precompensation=False)
        good = timing.prach_verdict(self.b.differential_ms, "format 0", 103.13,
                                    gnss_precompensation=True)
        self.assertFalse(bad["fits"])
        self.assertGreater(bad["residual_delay_us"], 1000)
        self.assertTrue(good["fits"])


class TestDuplex(unittest.TestCase):
    def test_tdd_guard_cannot_cover_a_leo_differential(self):
        far = slant_range_km(550, 10)
        b = timing.delay_budget(far, service_link_min_km=slant_range_km(550, 90))
        v = duplex.duplex_verdict(b.differential_ms, 71.35)
        self.assertFalse(v["tdd_feasible"])
        self.assertEqual(v["recommendation"], "FDD")
        self.assertLess(v["tdd_cell_radius_km"], 50)

    def test_a_long_enough_guard_allows_tdd(self):
        v = duplex.duplex_verdict(0.02, 71.35)
        self.assertTrue(v["tdd_feasible"])
        self.assertEqual(v["recommendation"], "TDD")


class TestORAN(unittest.TestCase):
    def test_option8_needs_gigabits(self):
        r = oran.split_verdict("option8", sample_rate_msps=30.72, antenna_ports=2,
                               feeder_capacity_bps=500e6)
        self.assertGreater(r["fronthaul_bps"], 1e9)
        self.assertFalse(r["fits_feeder"])

    def test_split_reduces_feeder_load_monotonically(self):
        a = oran.split_verdict("option8", sample_rate_msps=30.72, antenna_ports=2)
        b = oran.split_verdict("option7-2x", used_subcarriers=1272,
                               symbols_per_second=28000)
        c = oran.split_verdict("option2", user_throughput_bps=100e6)
        self.assertGreater(a["fronthaul_bps"], b["fronthaul_bps"])
        self.assertGreater(b["fronthaul_bps"], c["fronthaul_bps"])

    def test_onboard_load_flags_space_qualified_baseband(self):
        self.assertTrue(oran.onboard_processing_load("option2")["harq_closes_onboard"])
        self.assertFalse(oran.onboard_processing_load("option8")["harq_closes_onboard"])

    def test_unknown_split_declares(self):
        self.assertIsInstance(oran.split_verdict("option99"), Unknown)


class TestHandover(unittest.TestCase):
    def test_cadence_matches_beam_dwell(self):
        d = beam_dwell_s(550, beam_diameter_km(550, 40))
        c = timing.handover_cadence_s(d)
        self.assertAlmostEqual(c["handover_every_s"], round(d, 2), places=2)
        self.assertGreater(c["handovers_per_hour"], 20)


if __name__ == "__main__":
    unittest.main()
