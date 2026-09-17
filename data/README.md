# data — published tables, populated by hand, with provenance

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.

These files are empty. That is the design.

The ITU-R coefficients they hold are published tables. Typing them from memory
produces numbers that look right, propagate through every high-band link budget
in the repository, and cannot be traced back to anything. So the loader refuses a
table with no rows, and also refuses one with rows but no `populated_by` and
`retrieved_utc` — a table without provenance is not a table, it is a guess with
a filename.

To populate one: take the values from the recommendation, keep the column order,
record who you are and when you did it, and run

    python3 -m unittest discover -s tests

Four tests in `tests/test_atmosphere.py` are skipped while the table is empty and
run once it is not. One of them asserts that extrapolation outside the loaded
range is still refused.
