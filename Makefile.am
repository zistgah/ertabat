# © 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
ACLOCAL_AMFLAGS = -I m4

pkgpythondir = $(pythondir)/ertabat

nobase_dist_pkgpython_PYTHON = \
	src/ertabat/__init__.py src/ertabat/cli.py src/ertabat/dispatch.py \
	src/ertabat/link/__init__.py src/ertabat/link/budget.py \
	src/ertabat/link/modulation.py src/ertabat/link/geometry.py \
	src/ertabat/link/atmosphere.py \
	src/ertabat/ntn/__init__.py src/ertabat/ntn/timing.py \
	src/ertabat/ntn/duplex.py src/ertabat/ntn/oran.py \
	src/ertabat/hal/__init__.py src/ertabat/hal/base.py src/ertabat/hal/devices.py \
	src/ertabat/hal/stub.py src/ertabat/hal/registry.py src/ertabat/hal/conformance.py \
	src/ertabat/bom/__init__.py src/ertabat/bom/model.py src/ertabat/bom/providers.py \
	src/ertabat/bom/lookup.py src/ertabat/bom/report.py \
	src/ertabat/sota/__init__.py src/ertabat/sota/registry.py

dist_bin_SCRIPTS = bin/ertabat

dist_doc_DATA = README.md CONTRACT.md CONTEXT.md AGENTS.md MANIFEST.yaml
EXTRA_DIST = tests ops docs skills bom data m4

check-local:
	PYTHONPATH=$(srcdir)/src $(PYTHON) -m unittest discover -s $(srcdir)/tests -v
	bash $(srcdir)/ops/verify.sh
	bash $(srcdir)/ops/selftest.sh

resume:
	bash $(srcdir)/ops/resume.sh

.PHONY: resume
