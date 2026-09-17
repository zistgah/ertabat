#!/usr/bin/env bash
# ertabat self-test — runs the suite and the CLI, and proves the honesty gates bite.
# © 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="src:${PYTHONPATH:-}"
P=0; F=0
ok(){ printf '  \033[32m✓\033[0m %s\n' "$1"; P=$((P+1)); }
no(){ printf '  \033[31m✗\033[0m %s\n' "$1"; F=$((F+1)); }
chk(){ local d="$1"; shift; if "$@" >/dev/null 2>&1; then ok "$d"; else no "$d"; fi; }
chkfail(){ local d="$1"; shift; if "$@" >/dev/null 2>&1; then no "$d (it did NOT refuse)"; else ok "$d"; fi; }

printf '\n  unit suite\n'
if python3 -m unittest discover -s tests -q >/dev/null 2>&1; then
  ok "$(python3 -m unittest discover -s tests -q 2>&1 | grep -oE 'Ran [0-9]+ tests' ) pass"
else
  no "unit suite"; python3 -m unittest discover -s tests 2>&1 | tail -20
fi

printf '\n  the gates bite\n'
chkfail "a link budget with no atmosphere does not close" \
  python3 -m ertabat.cli link --tx-power-dbw 0 --tx-gain-dbi 2 --altitude-km 550 \
    --freq-mhz 437 --rx-gain-dbi 18 --system-noise-temp-k 250 --data-rate-bps 9600 \
    --modulation QPSK
chk "the same budget closes once the atmosphere is declared" \
  python3 -m ertabat.cli link --tx-power-dbw 0 --tx-gain-dbi 2 --altitude-km 550 \
    --freq-mhz 437 --rx-gain-dbi 18 --system-noise-temp-k 250 --data-rate-bps 9600 \
    --modulation QPSK --atmospheric-loss-db 1.0
chkfail "an unpriced BoM line blocks a clean exit" \
  python3 -m ertabat.cli bom bom/cubesat-1u-lband.csv --price-book /nonexistent
chkfail "Option 8 does not fit a 500 Mbps feeder" \
  python3 -m ertabat.cli oran --split option8 --sample-rate-msps 30.72 \
    --antenna-ports 2 --feeder-capacity-bps 500000000
chk "an unbound radio still self-describes" python3 -m ertabat.cli hal --device rtlsdr-v3
chk "doctor reports what is absent" python3 -m ertabat.cli doctor
chk "dispatch emits the packets" python3 -m ertabat.cli dispatch

printf '\n  surfaces\n'
for c in "pass --altitude-km 550 --freq-mhz 437" "ntn --altitude-km 550 --gnss" \
         "sota" "hal" "bom bom/ground-station-sdr.csv --status"; do
  chk "ertabat $c" python3 -m ertabat.cli $c
done

printf '\n  %s passed · %s failed\n\n' "$P" "$F"
[ "$F" -eq 0 ]
