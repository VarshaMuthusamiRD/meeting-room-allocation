# Meridian Coworking - Meeting Room Booking & Utilisation Service

An offline booking system for Meridian Coworking's four meeting rooms,
built to RFP MCW-2026-014. Replaces the front-desk paper diary with a
system that refuses double-bookings and rule-breaking requests at the
point of booking, and answers the utilisation question behind the
Boardroom's June lease renewal.

## Quick start

    python run.py add-room Huddle 6
    python run.py book Huddle 2026-03-02 09:00 10:00 4 rsingh
    python run.py report-utilisation 2026-03-02
    python run.py -h        # every command and its arguments

See **HANDOVER.md** for full install/run/backup/troubleshooting
instructions, **CLAUDE.md** for the codebase structure and conventions,
**ASSUMPTIONS.md** for how the twelve deliberate RFP gaps were resolved,
**TRACEABILITY.md** for the full requirement-to-test map, **ROBUSTNESS.md**
and **REVIEW.md** for the Day-19 hardening/self-review pass, **LIMITATIONS.md**
for what is not built, and **BOARDROOM_FINDING.md** for the utilisation
answer the whole tender was commissioned to produce.

## Status
All 40 must-have requirements (F1-F40), all 16 business rules, and all 42
acceptance criteria from the RFP are implemented and tested: 101 tests,
all green. Tagged `v1.0`. Should-have/could-have requirements (F41-F48)
were not attempted -- see LIMITATIONS.md.

    python -m unittest discover -s tests -v
