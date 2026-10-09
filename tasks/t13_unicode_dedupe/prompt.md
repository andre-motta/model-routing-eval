`contacts.dedupe(records)` is supposed to merge records that refer to the same person:
same email (case-insensitive) or same name (ignoring case, accents and whitespace
differences). Support reports duplicates still showing up for customers with accented
names, names typed on a Mac vs. on Windows, and German names with "ß" vs "ss".
`tests/test_dedupe.py` has one reproduction. Find all root causes, fix them in the
library (not in the test), keep the first-seen record as the survivor, and run the
tests.
