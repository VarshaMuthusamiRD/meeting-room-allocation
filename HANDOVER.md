# HANDOVER.md

## How to install
No installation step beyond having Python 3.11+ on the machine (TC6: it
must run on a machine with only the language runtime installed -- no
third-party packages are required, standard library only per TC3).
1. Copy this repository onto the desk machine.
2. Confirm Python is available: `python --version`.
That is the whole install.

## How to run
Single documented command (TC5): from the repository root,

    python run.py <command> [arguments...]

Global options (`--data-dir`, `--config`, `--now`) go **before** the
subcommand name, e.g.:

    python run.py --now "2026-03-02 08:35" cancel 3

Run `python run.py -h` at any time to see every available command and its
arguments (F38). A few examples front desk staff will use most often:

    python run.py book Huddle 2026-03-02 09:00 10:00 4 rsingh
    python run.py cancel 7
    python run.py list-date 2026-03-02
    python run.py report-utilisation 2026-03-02
    python run.py check

Every command exits 0 on success and 1 on refusal/failure (F37), and every
refusal is printed with the exact rule that caused it, e.g.
`REFUSED: [BR1] Overlaps an existing booking in this room.`

## Where data lives
- `data/bookings.json` -- rooms, bookings, closures. Human-readable JSON
  (TC4); safe to open and inspect, but should not be hand-edited while the
  program is running.
- `data/audit.log` -- one JSON line per accepted or refused attempt,
  append-only (TC12). This is the record to check in a dispute.
- `data/backups/` -- the 3 most recent timestamped copies of
  `bookings.json`, written automatically before every save (F31).

None of these are committed to git (see `.gitignore`) -- they are runtime
state, generated fresh on the machine that runs the system, not source.

## How to back up and restore the data file
A backup is taken automatically before every save. To see what is
available and restore one by hand:

    python run.py list-backups
    python run.py restore-backup data/backups/bookings.20260302T090000123456.json

## What to do when it will not start
1. Run `python run.py check`. This runs the startup self-check (F34): it
   confirms the data file is present, readable, and structurally valid,
   and prints a clear diagnostic if not (F30) rather than crashing.
2. If `check` reports the data file is corrupted or hand-edited into an
   invalid state, restore the most recent backup (`list-backups` then
   `restore-backup`) and re-run `check`.
3. If there is no data file at all yet, that is normal on a brand-new
   install -- `check` reports OK and the file is created on first save
   (the first `add-room` or `book`).
4. Run `python run.py version` to confirm the software and data format
   version (F36) if you suspect a mismatch between the code and an old
   data file from a previous version.
5. If none of the above resolves it, `python -m unittest discover -s
   tests` from the repository root should be all-green on an unmodified
   checkout; a red suite points at a local code change, not the data.

## Configuration
`config.json` in the repository root controls opening hours, booking
length limits, and the daily per-person limit (F35/TC9) -- edit this file,
never the code, to change these (AC39). Restart the program to pick up a
change (there is no live-reload; TC5 already gives a single restart-friendly
command).
