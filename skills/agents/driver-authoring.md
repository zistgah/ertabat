# Writing a radio driver for ertabat

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.

You need: the device, its host library, and `src/ertabat/hal/base.py`.

## The contract

Subclass `RadioDevice`. Implement every abstract method. Then the part that
decides whether your driver is accepted:

    def read_iq(self, n):
        if not self._handle:
            raise NotFitted("<key>: device not open")
        ...                    # real samples, or raise

`read_iq` returns samples that came from hardware, or it raises `NotFitted`. It
never returns zeros, never returns noise it generated, never replays a capture
without saying so. `capabilities()` reports `receive` as present only when a
handle is open.

## Registering

    from ertabat.hal.registry import register
    register("rtlsdr-v3", lambda spec, **kw: RtlSdrRadio(spec, **kw))

The key must already exist in `hal/devices.py`. If your device is not there, add
the `DeviceSpec` first, with `unknowns` listing every figure the datasheet does
not publish. A spec with no unknowns is usually a spec someone guessed at.

## Proving it

    from ertabat.hal.conformance import check_driver, verdict
    print(verdict(check_driver(MyRadio(SPECS["my-key"]), hardware_present=False)))

With no hardware attached the harness expects refusals. It is mutation-tested
against a driver that fabricates samples, so a pass means something. Include the
verdict in your pull request, and add a test that fails when your driver's
refusal is removed.

## Doppler

Do not build Doppler correction into the driver. `hal/base.doppler_corrected_tuning`
computes the target and refuses when the tuner cannot reach it; the driver's job
is to tune where it is told and to report honestly when it cannot.
