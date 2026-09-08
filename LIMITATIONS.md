# LIMITATIONS.md

What is not built, what is known to be imperfect, and what a next team
would want to look at. Started during Day-19 hardening; extended at
handover with anything found in the final operability pass.

## Known, accepted limitations

- **No input length cap on audit log entries.** A booker id or room name
  can be arbitrarily long before other rules (BR13, BR15) refuse it, and
  every attempt -- accepted or refused -- is logged in full (TC12 requires
  completeness, not a size cap). In a real deployment with adversarial
  input this could grow `audit.log` faster than expected. Not fixed,
  because the RFP does not ask for an input-length limit anywhere in
  Section 6/7, and adding an undiscussed one risks silently truncating a
  legitimate long value. Flagged in REVIEW.md rather than fixed unilaterally.

- **Backup filenames use microsecond-precision timestamps.** Two saves
  within the same microsecond would collide and one backup could overwrite
  the other. Not a realistic risk for a single front-desk process handling
  one request at a time (TC1/TC6 assume exactly that), so left as is rather
  than adding collision-proofing the RFP never asked for.

- **No true concurrency control.** The system is a single-process CLI; if
  two people ran it against the same data file from two terminals at
  literally the same moment, the last writer wins (see G5 in
  ASSUMPTIONS.md). This matches the RFP's stated environment (one desk,
  one machine, TC1) and was not built for multi-writer use because
  multi-writer use was never in scope.

- **Occasional test-suite flakiness observed during development, not
  reproduced since.** Once, out of dozens of consecutive full-suite runs
  during Phase 3, `python -m unittest discover -s tests` reported a single
  error that did not reappear on immediate re-run (5/5 clean afterward).
  Most likely explanation is transient Windows filesystem/antivirus
  interference on the temporary directories the tests create and delete
  rapidly, not a defect in the code under test -- no failure could be
  pinned to a specific assertion or reproduced deliberately. Worth a second
  look if it recurs with a specific, reproducible test name.

## Not built (out of scope by Section 5, or should/could-have not reached)
See Section 5 of the RFP for the full out-of-scope list (logins, email,
recurring bookings, billing, desks, GUI, multi-site) -- none of it was
built, as instructed.

**Should-have requirements F41-F44 are now built and tested** (smallest-
room suggestion, under-occupancy warning, day timeline, single-op room
move) -- added after the must-have submission was complete, so nothing was
half-built at handover time. See TRACEABILITY.md for their tests.

**Could-have requirements F45-F48 were not attempted** (weekly summary,
accountant export, waiting list, trend comparison), matching the RFP's own
stated preference: "we will mark you down for a broken attempt" at a
could-have (Section 4.7). If a next team picks this up, F45 (weekly
summary) is the most natural next addition given `reports.py` already has
`room_utilisation_range` to build on.
