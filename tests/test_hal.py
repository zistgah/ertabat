"""Radio HAL honesty, including the mutant driver the harness must catch.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
"""
import unittest

from ertabat import Unknown
from ertabat.hal.base import Capability, NotFitted, RadioDevice, doppler_corrected_tuning
from ertabat.hal.conformance import check_driver, verdict
from ertabat.hal.devices import SPECS, by_frequency
from ertabat.hal.registry import census, open_device, register
from ertabat.hal.stub import StubRadio


class LiarRadio(RadioDevice):
    """A driver that fakes a signal. The harness has to catch this one.

    It is here as a mutant: if check_driver ever passes it, the honesty check
    has stopped biting and every conformance result in the repo is worthless.
    """

    def __init__(self, spec):
        self.spec = spec

    def capabilities(self):
        return (Capability("receive", True, "claims hardware it does not have"),)

    def open(self): pass
    def close(self): pass
    def set_frequency(self, hz): pass
    def set_sample_rate(self, sps): pass
    def set_gain(self, db): pass
    def read_iq(self, n): return [0j] * n
    def write_iq(self, samples): return len(samples)


class TestStubHonesty(unittest.TestCase):
    def test_stub_refuses_to_produce_samples(self):
        d = open_device("rtlsdr-v3")
        d.open()
        with self.assertRaises(NotFitted):
            d.read_iq(1024)

    def test_stub_refuses_to_transmit(self):
        with self.assertRaises(NotFitted):
            open_device("hackrf-one").write_iq([0j])

    def test_stub_records_settings_without_claiming_to_apply_them(self):
        d = open_device("rtlsdr-v3")
        d.set_frequency(437e6)
        self.assertIn("nothing was applied", d.state()["note"])

    def test_stub_still_rejects_an_impossible_tune(self):
        with self.assertRaises(ValueError):
            open_device("rtlsdr-v3").set_frequency(12e9)


class TestConformanceBites(unittest.TestCase):
    def test_the_honest_stub_passes(self):
        v = verdict(check_driver(StubRadio(SPECS["rtlsdr-v3"])))
        self.assertTrue(v["passed"], v["failures"])

    def test_a_fabricating_driver_fails(self):
        """Mutation test: the liar must be caught, and for the right reason."""
        v = verdict(check_driver(LiarRadio(SPECS["rtlsdr-v3"])))
        self.assertFalse(v["passed"])
        self.assertTrue(any("invent" in f for f in v["failures"]), v["failures"])
        self.assertTrue(any("receive" in f for f in v["failures"]), v["failures"])


class TestRegistry(unittest.TestCase):
    def test_unknown_device_declares(self):
        self.assertIsInstance(open_device("no-such-radio"), Unknown)

    def test_census_reports_stubs_honestly(self):
        c = census()
        self.assertTrue(all(v in ("stub", "driver") for v in c.values()))
        self.assertIn("rtlsdr-v3", c)

    def test_register_refuses_a_device_with_no_spec(self):
        with self.assertRaises(KeyError):
            register("invented-radio", lambda spec: None)


class TestCoverage(unittest.TestCase):
    def test_frequency_coverage_is_real(self):
        keys = [s.key for s in by_frequency(437e6)]
        self.assertIn("rtlsdr-v3", keys)
        self.assertNotIn("lnb-ku-universal", keys)

    def test_doppler_tuning_refuses_out_of_range(self):
        d = open_device("rtlsdr-v3")
        self.assertEqual(doppler_corrected_tuning(d, 437.5e6, -10000.0), 437510000.0)
        self.assertIsInstance(doppler_corrected_tuning(d, 12.5e9, 0.0), Unknown)

    def test_the_lnb_is_not_sold_as_a_radio(self):
        s = SPECS["lnb-ku-universal"]
        self.assertFalse(s.transmit)
        self.assertEqual(s.max_sample_rate_sps, 0.0)
        self.assertIn("not a payload", s.notes)

    def test_the_flight_class_declares_its_unknowns(self):
        self.assertTrue(SPECS["flight-sdr-class"].unknowns)


if __name__ == "__main__":
    unittest.main()
