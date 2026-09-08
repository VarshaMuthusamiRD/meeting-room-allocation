# CLAUDE.md

Guidance for anyone (human or AI) working in this repository.

## Purpose
An offline meeting room booking and utilisation service for Meridian
Coworking, built to RFP MCW-2026-014. See the RFP docx in the repo root for
the full specification; ASSUMPTIONS.md for the twelve deliberate gaps we
answered; TRACEABILITY.md for which tests cover which requirement/rule.

## Commands
- Run the CLI: `python run.py <command> [args...]` (global flags
  `--data-dir`, `--config`, `--now` go *before* the subcommand name).
- Run all tests: `python -m unittest discover -s tests -v`
- See every available command: `python run.py -h`

## Structure
- `src/mrbooking/` - the package.
  - `models.py` - Room, Booking, Closure dataclasses.
  - `storage.py` - JSON persistence, atomic writes, backup rotation,
    corruption detection.
  - `rules.py` - BR1-BR16 business rule engine.
  - `service.py` - orchestrates storage + rules for every F1-F16 operation,
    plus input validation (F25-F28).
  - `reports.py` - F17-F24 reporting, verified against Appendix B exactly.
  - `audit.py` - append-only audit log.
  - `config.py` / `clock.py` - configuration and the injectable clock.
  - `cli.py` - argparse entry point.
- `tests/` - unittest suite. Test names always embed the requirement or rule
  id they cover (`test_F1_...`, `test_BR7_...`) so TRACEABILITY.md can point
  straight at them.
- `data/` - runtime data (`bookings.json`, `audit.log`, `backups/`); not
  committed (see `.gitignore`) since it is generated at runtime.
- `config.json` - opening hours, booking length limits, and the daily
  per-person limit (F35/TC9). Never hardcode these in source.

## Conventions
- Every refusal raises `mrbooking.errors.RuleViolation(rule_id, message)`
  and is caught at the CLI/service boundary; `rule_id` is always one of
  BR1-BR16 or F25-F28 and is always shown to the caller (F2/AC15 - "Invalid
  booking" alone is never an acceptable message).
- When more than one rule is broken by a single request, the rule engine
  reports the first one violated in fixed BR-numeric order (see G7 in
  ASSUMPTIONS.md).
- The current date/time is never read directly from the system clock inside
  business logic; it always comes through the injected `Clock` (TC7), so
  that BR6/BR8/BR11 are reproducible in tests and demos via `--now`.
- Standard library only. Any new dependency must be justified here before
  it is added; none has been needed so far.
- Cancelled bookings are never deleted from the data file - they are kept
  with `status: "cancelled"` for audit history, and excluded from overlap
  checks, daily-limit counts, and utilisation figures (see G1/G3).

## Things that keep going wrong
- argparse subparsers: global options (`--data-dir`, `--now`, `--config`)
  must be passed *before* the subcommand, e.g.
  `python run.py --now "2026-03-02 08:35" cancel 3`, not after.
- Windows paths: this repo is developed on Windows; prefer `pathlib.Path`
  everywhere in source so tests behave the same on any OS.
