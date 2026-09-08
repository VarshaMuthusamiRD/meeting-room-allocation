# Boardroom utilisation finding

Based on the demonstration run against the Appendix A sample data for
2 March 2026 (one day's evidence -- see caveat below).

## The numbers

| Room | Capacity | Booked minutes | Room utilisation | Seat utilisation contribution |
|---|---|---|---|---|
| Focus 1 | 2 | 15 | 2.1% | 15 min x 1 attendee |
| Focus 2 | 2 | 0 | 0.0% | none |
| Huddle | 6 | 195 | 27.1% | 195 min across 3 bookings |
| Boardroom | 14 | 720 | **100.0%** | 720 min across 3 bookings |

Building-wide seat utilisation for the day: **54.3%** (9,375 of 17,280
seat-minutes).

## The finding

**By room-utilisation alone, the Boardroom looks like the best-used room in
the building: 100.0%, fully booked all day.** That number is the one that
would justify keeping it exactly as it is.

But room utilisation only asks "was the room occupied," not "was it full."
Looking at who actually used it that day:
- 08:00-12:00: 12 of 14 seats (mbaker) -- reasonably full.
- 12:00-16:00: 14 of 14 seats (mbaker) -- exactly at capacity.
- 16:00-20:00: 9 of 14 seats (tokafor) -- a little under two-thirds full.

On this particular day, none of the three Boardroom bookings were the
"one-to-one call in the fourteen-seat room" problem described in Section 2
-- every booking used at least 9 of 14 seats. **On this evidence, the
Boardroom is earning its floor space on 2 March 2026**: it was fully
booked, and the seat occupancy within those bookings was consistently high
(64%-100% of capacity), not the sparse two-person meetings that prompted
this tender.

The building-wide seat utilisation of 54.3% (against 32.3% room
utilisation across all four rooms, per Appendix B) shows the opposite
imbalance to what Section 2 worried about: on this day, when rooms were
booked, they tended to be well-filled overall, and the Boardroom was the
most consistently well-filled room of the four.

## The caveat

**This is one day of evidence, not a lease decision.** Section 2's actual
complaint -- a fourteen-seat room "used by two people while others are
turned away" -- did not appear in this sample data at all (the sample data
was deliberately constructed to be valid under every rule, not to
represent a typical or worst day). The system now makes this measurable
going forward: `python run.py report-range <start> <end>` gives the
Boardroom's average utilisation over any period once real bookings
accumulate, and `report-under-occupied` will surface exactly the kind of
booking Section 2 describes the moment one occurs. **Recommendation: run
`report-range` and `report-under-occupied` over several real weeks before
the June lease renewal, rather than deciding from a single sample day.**
The tooling to answer the question is now in place; the answer itself
needs real usage data, which a paper diary could never have produced.
