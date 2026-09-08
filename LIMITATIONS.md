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

**Should-have (F41-F44) and could-have (F45-F48) requirements were not
attempted.** All forty must-have requirements (F1-F40, BR1-BR16) are
complete, tested, and green (101 tests), matching the RFP's own stated
preference: "we would rather have the must-haves working properly than
these half-built" (Section 4.6) and "we will mark you down for a broken
attempt" at a could-have (Section 4.7). Rather than build any of F41-F48
partially in the time available, none were started, so that nothing
half-finished is being handed over. If a next team picks this up, F41
(smallest-room suggestion) and F43 (day timeline) look like the most
useful next additions given how `reports.py` and `service.py` are already
structured.
