# ROBUSTNESS.md

What was thrown at the system during the Day-19 hardening pass, what
happened, and what was changed as a result.

## Edge-case sweep (Section 6 boundaries)
Every rule in Section 6 has a stated boundary; both sides were tested
(see TRACEABILITY.md for the exact test names):
- BR1: bookings that touch exactly at a boundary are accepted; bookings
  that overlap by even one minute on either side are refused.
- BR2: exactly 15 minutes and exactly 240 minutes are accepted; 14 minutes
  and 241 minutes are refused.
- BR3: quarter-hour boundaries (09:00, 09:15...) are accepted; 09:07 is
  refused.
- BR4: 08:00 start and 20:00 end are accepted; anything crossing either
  boundary is refused.
- BR5: attendees exactly at room capacity are accepted; one over is
  refused.
- BR7: the third booking on a day is accepted, the fourth refused.
- BR8/BR11: cancelling or amending more than the cutoff before start is
  accepted; exactly at the cutoff is refused (the RFP states the boundary
  itself is "too late").
- BR15: capacity 1 and 50 accepted; 0 and 51 refused.
No behavioural changes were needed here -- the rule engine was written
against these boundaries from the start (see rules.py), and the sweep
confirmed it rather than finding a defect.

## Input-fuzzing sweep (tests/test_fuzz.py)
Every field of every write operation (create, amend, add-room) was fed:
`None`, empty string, whitespace-only string, an int where a string was
expected, a float, a bool, a list, a dict, a 10,000-character string, a
negative number, a non-existent date (`2026-13-40`, `2026-02-30`), and a
malformed time (`09:99`, `09:00:00`).

**Result: every one of these was refused with a `RuleViolation` (F25 in
almost every case); none produced an unhandled exception, a stack trace,
or a crash.** No code changes were required -- `_require_text`,
`_require_int`, `_validate_date`, and `_validate_time` in `service.py`
already reject anything that is not a well-typed, well-formed value before
it ever reaches the rule engine or the storage layer.

## Interrupted-save simulation (F29)
`storage.save` was forced to fail partway through (by making `os.replace`
raise) and the pre-existing data file was checked afterwards: it was
byte-for-byte unchanged and still valid JSON. This is a property of the
write-to-temp-file-then-replace design, not a special case that was added
after finding a bug.

**Update, found while building F45-F48:** a real, intermittent failure
that earlier phases had only guessed at (logged as unreproduced flakiness
in LIMITATIONS.md) was root-caused with a full traceback: `os.replace` can
transiently raise `PermissionError: [WinError 32]` on Windows when another
process briefly holds a lock on the just-written temp file (antivirus or
search indexing are the usual cause) - and the cleanup code in the
original `finally` block made it worse, masking that error with a second
one from a failed `os.remove` on the same locked file. Fixed with a
bounded retry (`storage._replace_with_retry`, 5 attempts with a short
backoff) and a cleanup path that can no longer hide the real error. The
full suite went from roughly 1-in-3 to 1-in-5 runs failing to 8+
consecutive clean runs after the fix. See
`test_F29_transient_windows_file_lock_is_retried_not_fatal` and
`test_F29_permanent_lock_still_raises_after_retries`.

## Corrupted / hand-edited data file (F30)
Three forms of corruption were tried against `storage.load`: invalid JSON
syntax, a JSON object missing required top-level keys, and a JSON object
with a field of the wrong type (`next_id` as a string). All three raise
`DataFileError` with a message naming the problem; none crash the process
or silently proceed with bad data. The `check` CLI command surfaces this
the same way at startup (F34).

## Performance (TC10)
A 10,000-booking data file was built (seeded directly for speed of test
setup, then saved through the normal `storage.save` path so the file on
disk is the same shape a live system would produce) and every user-facing
operation -- listing a date, generating the utilisation report, generating
a 6-month range report, creating a new booking, computing free periods, and
a full reload from disk -- was timed. All ran in well under the 2-second
budget (the slowest, a full test run of six such operations back to back,
took under 1.6 seconds combined on ordinary developer hardware).

## What this did not cover
No load/concurrency testing beyond the single-process assumption stated in
G5 -- the RFP explicitly scopes this as a single desk machine, single
front-desk operator, no network (TC1), so concurrent writers were not
considered a requirement.
