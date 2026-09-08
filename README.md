# Meridian Coworking - Meeting Room Booking & Utilisation Service

An offline command-line booking system for Meridian Coworking's four
meeting rooms, built end to end against **RFP MCW-2026-014**. It replaces
a paper diary at the front desk with a system that refuses double-bookings
and rule-breaking requests at the point of booking, tells staff exactly
which rule was broken when it does, and answers the utilisation question
behind the Boardroom's June lease renewal.

## Background

Meridian Coworking runs one building, sixteen desks, and four bookable
meeting rooms (Focus 1, Focus 2, Huddle, Boardroom) for around forty
members. Bookings were kept in a paper diary at the front desk, which
failed in three specific, measurable ways (RFP Section 2):

1. Two members occasionally wrote down the same room and time -> someone
   gets turned out of a room mid-meeting.
2. The fourteen-seat Boardroom gets booked for one-to-one calls while
   larger groups are turned away.
3. Nobody could measure how heavily each room was actually used - and the
   lease renewal in June needs to decide whether the Boardroom earns its
   floor space.

This system exists to fix all three, in that priority order (RFP Section
3, objectives O1-O4): no double-bookings ever, house rules enforced
automatically, room usage made measurable, and the whole thing usable by
front-desk staff after five minutes of explanation.

## What's implemented

**All forty-eight requirements in the RFP are built and tested** - every
must-have, should-have, and could-have. Each optional group was only
started once everything ahead of it was complete and green, per the RFP's
own stated preference for a fully working addition over a broken attempt
at one (Section 4.6/4.7).

| Group | Requirements | Status |
|---|---|---|
| Core booking, amendment, room admin | F1-F16 | Done |
| Reporting & analysis | F17-F24 | Done, verified exactly against Appendix B |
| Data integrity & resilience | F25-F33 | Done |
| Operability | F34-F40 | Done |
| Business rules | BR1-BR16 | Done, both sides of every boundary tested |
| Technical constraints | TC1-TC12 | Satisfied |
| Should-have | F41-F44 | Done |
| Could-have | F45-F48 | Done |
| Acceptance criteria | AC1-AC42 | All pass |

**139 unit tests, all green.** Tagged `v1.0` at the end of the must-have
build (see [TRACEABILITY.md](TRACEABILITY.md) for the full
requirement-to-test map).

## Business rules enforced

Every booking is checked against sixteen rules (RFP Section 6) before it
is accepted; a refusal always names the exact rule (F2/AC15 - "Invalid
booking" alone is never shown). Highlights:

- No two bookings may overlap in the same room, though back-to-back
  bookings that touch exactly are allowed (BR1).
- Bookings run 15 minutes to 4 hours, on the quarter hour, within 08:00-
  20:00 opening hours (BR2-BR4).
- Attendees must fit the room, one person may hold at most 3 bookings a
  day, and nothing can be booked in the past (BR5-BR7).
- Cancellations and amendments must happen more than an hour before the
  booking starts; an amendment that changes nothing is refused (BR8, BR11,
  BR16).
- Room names are unique regardless of case/spacing, booker ids are
  3-20 lower-case letters/digits, and a room with existing bookings can't
  be closed out from under them (BR12-BR14).

Full rule text and every boundary case: [ASSUMPTIONS.md](ASSUMPTIONS.md)
and [ROBUSTNESS.md](ROBUSTNESS.md).

## Technical constraints

Per RFP Section 7: runs entirely offline (TC1), no paid services or API
keys (TC2), Python standard library only (TC3), data persists in a single
human-readable JSON file with a format version (TC4/TC8), starts with one
documented command (TC5) on a machine with only the Python runtime
installed (TC6), the current time is injectable for reproducible testing
(TC7), configuration lives outside the code (TC9), every operation
completes in under two seconds against 10,000 bookings (TC10), all times
are local with no time zone handling (TC11), and the audit log is
append-only (TC12).

## Quick start

Requires Python 3.11+ and nothing else - no install step, no third-party
packages.

    python run.py add-room Huddle 6
    python run.py book Huddle 2026-03-02 09:00 10:00 4 rsingh
    python run.py report-utilisation 2026-03-02
    python run.py -h        # every command and its arguments

Global options (`--data-dir`, `--config`, `--now`) go *before* the
subcommand name:

    python run.py --now "2026-03-02 08:35" cancel 3

## Command reference

| Category | Commands |
|---|---|
| Booking | `book`, `cancel`, `get`, `list-date`, `list-room`, `list-booker`, `amend` |
| Room admin | `add-room`, `list-rooms`, `close-room`, `free-periods` |
| Reporting | `report-utilisation`, `report-minutes`, `report-seat-utilisation`, `report-peak`, `report-under-occupied`, `report-range`, `report-booker`, `report-empty` |
| Should-have | `suggest-room`, `timeline`, `move` |
| Could-have | `report-weekly`, `export`, `waitlist-add`, `waitlist-list`, `waitlist-remove`, `report-trend` |
| Operability | `version`, `check`, `list-backups`, `restore-backup` |

Every command exits `0` on success and `1` on refusal or failure (F37),
and `python run.py -h` lists every command with its exact arguments
(F38).

## Project structure

    run.py                  single entry point (TC5)
    config.json              opening hours, booking limits (F35/TC9)
    src/mrbooking/
      models.py               Room, Booking, Closure
      storage.py               JSON persistence, atomic writes, backups
      rules.py                  BR1-BR16 rule engine, free_rooms (F41)
      service.py                 orchestrates every F1-F16/F41/F42/F44 op
      reports.py                  F17-F24 reporting, day_timeline (F43)
      audit.py                     append-only audit log
      config.py / clock.py          config loading, injectable clock
      cli.py                          argparse entry point
    tests/                    unittest suite, one file per requirement group
    data/                    runtime data (gitignored - generated, not source)

## Configuration

`config.json` controls opening hours, booking length limits, and the
daily per-person limit - never hardcoded (F35/TC9). Edit the file, not the
code, and restart to pick up a change.

## Testing

    python -m unittest discover -s tests -v

Every test name embeds the requirement or rule id it covers
(`test_F1_...`, `test_BR7_...`), so [TRACEABILITY.md](TRACEABILITY.md) can
point straight at the test proving each one.

## Documentation

| File | Covers |
|---|---|
| [HANDOVER.md](HANDOVER.md) | Install, run, backup/restore, troubleshooting |
| [CLAUDE.md](CLAUDE.md) | Codebase structure and conventions |
| [ASSUMPTIONS.md](ASSUMPTIONS.md) | How the twelve deliberate RFP gaps (Section 12) were resolved |
| [TRACEABILITY.md](TRACEABILITY.md) | Every requirement/rule/AC mapped to its test |
| [ROBUSTNESS.md](ROBUSTNESS.md) | The Day-19 edge-case and input-fuzzing sweep |
| [REVIEW.md](REVIEW.md) | Self-review pass (standing in for the RFP's peer-team exchange) |
| [LIMITATIONS.md](LIMITATIONS.md) | What isn't built and known imperfections |
| [BOARDROOM_FINDING.md](BOARDROOM_FINDING.md) | The utilisation answer this tender was commissioned to produce |
| `RFP_MCW-2026-014_Meeting_Room_Booking_Service.docx` | The original specification everything above traces back to |

## Out of scope

Per RFP Section 5: no user accounts or logins (a booker is just a text
id), no email/notifications, no recurring bookings, no billing, nothing
about desks, no GUI, no multi-site support. None of it was built.

## Status

**All 48 requirements in the RFP - every must-have, should-have, and
could-have - are implemented and tested: 141 tests, all green.** Tagged
`v1.0` at the end of the must-have build. See
[BOARDROOM_FINDING.md](BOARDROOM_FINDING.md) for the answer to the
question the RFP was actually commissioned to settle.
