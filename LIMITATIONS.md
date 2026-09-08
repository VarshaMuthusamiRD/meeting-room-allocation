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

- **Fixed: intermittent `WinError 32` on save, root-caused during the
  F45-F48 build.** Earlier phases noted unreproduced test-suite flakiness
  and guessed at antivirus/filesystem interference; while adding F45-F48,
  the real cause was captured with a full traceback: `os.replace` in
  `storage.save` can transiently raise `PermissionError: [WinError 32] The
  process cannot access the file` when another process (antivirus, search
  indexing) briefly holds a lock on the just-written temp file. The
  original code also had a second bug: its `finally` cleanup tried
  `os.remove` on that same locked file, which raised a second exception
  that masked the real one. Fixed in `storage._replace_with_retry`: up to
  5 retries with a short backoff on `PermissionError` (not a genuine
  conflict on the single-process desk machine TC1/TC6 assume), and the
  cleanup path no longer masks a real save failure. Covered by
  `test_F29_transient_windows_file_lock_is_retried_not_fatal` and
  `test_F29_permanent_lock_still_raises_after_retries` in
  `tests/test_integrity.py`. The full suite ran clean across 8+ consecutive
  runs after the fix, versus roughly 1-in-3 to 1-in-5 failing before it.

## Not built (out of scope by Section 5, or should/could-have not reached)
See Section 5 of the RFP for the full out-of-scope list (logins, email,
recurring bookings, billing, desks, GUI, multi-site) -- none of it was
built, as instructed.

**Should-have requirements F41-F44 are now built and tested** (smallest-
room suggestion, under-occupancy warning, day timeline, single-op room
move) -- added after the must-have submission was complete, so nothing was
half-built at handover time. See TRACEABILITY.md for their tests.

**Could-have requirements F45-F48 are now built and tested** (weekly
summary, accountant export, waiting list, trend comparison) -- again added
only after everything ahead of them was complete, tested, and green, per
the RFP's stated preference for a fully working addition over a broken
attempt at one (Section 4.7). All forty-eight requirements in the RFP are
now implemented.

## Design notes on the waiting list (F47)

- **No automatic promotion.** When a booking that a waitlist entry was
  queued against is cancelled, the entry is not automatically converted
  into a real booking. F47 only asks that a member be "recorded as wanting
  a slot" - it does not ask for automatic promotion, and building one would
  mean deciding *which* waiting member wins a freed slot (first-come? most
  senior? largest group?) - a genuine new business rule the RFP never
  specifies. Front desk staff check `waitlist-list` and rebook manually.
- **No notification.** Section 5 explicitly excludes "email, calendar
  invitations, or notifications of any kind" - so a promoted or expired
  waitlist entry is never emailed or otherwise announced. This is a direct
  consequence of an existing scope boundary, not a new one.
- **Waitlisting does not require an actual conflict.** `waitlist-add`
  checks the request is well-formed (duration, quarter-hour, opening
  hours, capacity, not in the past, booker id) but does not first verify
  the target slot is genuinely taken. Requiring that would mean re-running
  the full overlap check just to reject the case where it *would* pass -
  simpler and just as correct to let a member queue pre-emptively; nothing
  in F47 forbids it.
