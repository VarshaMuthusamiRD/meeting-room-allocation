# REVIEW.md

RFP Section 9 (Day 19) asks for a repository exchange with another team,
review against the RFP rather than against the reviewer's own design, and a
written response to every point. This is a solo-supplier build, so there is
no second team; per the adaptation agreed up front, this review was done by
re-reading the RFP end to end against the finished Day-18 code, deliberately
looking for places the implementation might satisfy its own tests while
missing what Section 6/7/8 actually asked for.

## Points raised and responses

**1. Two unused imports (`dataclasses.replace` in `service.py`,
`datetime` in `cli.py`).**
Response: accepted, removed. Dead imports are exactly the kind of thing
Section 10's "engineering process" scoring cares about; no reason to carry
them into `v1.0`.

**2. F7/F8 duplicate F17/F18 in the RFP's own numbering -- were they
implemented twice?**
Response: no, and this is worth stating explicitly. `reports.py` implements
the utilisation and minutes/count logic once; `TRACEABILITY.md` maps both
requirement pairs to the same functions rather than pretending they are
separate features. Declined to add a second implementation -- that would be
the "broken attempt at extra work" Section 4.7 warns against, not what
Section 4.3 is asking for.

**3. Does BR7's daily-limit count correctly exclude cancelled bookings, and
is that tested at the boundary (exactly 3, not just "some number")?**
Response: yes on both counts --
`test_BR7_fourth_booking_same_day_refused` books exactly three then checks
the fourth is refused, and `_active_bookings_for_booker_date` filters on
`status == "active"`, so a cancelled booking never occupies a limit slot
(G1). No change needed.

**4. The audit log accepts arbitrarily large request payloads (the fuzz
sweep intentionally threw a 10,000-character string at it) -- could that
bloat `audit.log` in a real deployment?**
Response: accepted as a known limitation rather than fixed now. TC12
requires the log to be append-only and complete, not size-capped, and the
RFP does not ask for input length limits on booker ids or room names beyond
BR13/BR15 (which are enforced and refuse before anything is logged as
accepted). Noted in LIMITATIONS.md instead of adding an unrequested
truncation rule that the RFP never asked for.

**5. `storage._rotate_backups` names backups with a microsecond-precision
timestamp -- could two saves in the same microsecond collide and silently
drop a backup?**
Response: theoretically yes, practically not a real risk for a single
front-desk process handling one operation at a time (TC1/TC6 assume a
single desk machine, not a high-throughput server); not worth the added
complexity of a collision-proofing scheme the RFP never asked for. Noted in
LIMITATIONS.md for completeness rather than silently ignored.

**6. Is BR16 (no-op amendment refused) checked *after* every other rule, so
that an amendment which is both unchanged and, say, over capacity reports
the capacity problem first per G7's fixed-order rule?**
Response: confirmed correct by re-reading `rules.check_amendment` -- BR16 is
the last check in the function, consistent with it being BR16 (the highest
numbered rule) in the fixed BR-numeric ordering agreed in G7. No change
needed.

## Outcome
Two points accepted and fixed (unused imports); four points investigated
and found to already be correct, or accepted as documented, scope-respecting
limitations rather than undiscussed gaps. No BR/F/AC-level defects were
found in the Day-18 core during this pass. The full suite (93 tests) is
green after the fixes above.
