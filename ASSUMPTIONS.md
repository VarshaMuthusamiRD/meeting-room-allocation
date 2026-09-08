# ASSUMPTIONS.md

Answers to the twelve deliberate gaps in Section 12 of RFP MCW-2026-014,
decided up front and built to consistently.

## G1 - Does a cancelled booking still count toward the 3-per-day limit?
**No.** Cancelled bookings are excluded from the count. A member who cancels
should not be penalised for a slot they no longer hold; the front desk
expectation is "3 active bookings," not "3 attempts."

## G2 - Does the attendee count include the booker?
**Yes.** Attendees means everyone physically in the room, including the
person who made the booking. This matches how capacity is used in practice
("this room seats N people") and keeps BR5 simple: attendees must not exceed
room capacity, full stop.

## G3 - Should cancelled bookings appear in the utilisation figures?
**No.** A cancelled booking never happened as far as the room's usage is
concerned; the minutes it would have used are free again. Reporting is
about the Boardroom's real usage, not requests that were later withdrawn.

## G4 - Should a room with no bookings appear in the report, or be omitted?
**Appear, at 0.0%.** Omitting an empty room would hide the very evidence the
lease decision needs (Focus 2 reads 0.0% in Appendix B and that is exactly
the point).

## G5 - If two bookings are submitted for the same slot at the same moment, which wins?
**First processed, in submission order.** This is a single-process CLI with
no concurrent writers, so requests are naturally serialised; the first one
to reach the rule engine is checked against an empty slot and accepted, the
second sees the first as an existing booking and is refused under BR1.

## G6 - Should the report cover only rooms, or also a building-wide figure?
**Rooms only.** The RFP's requirements (F17-F24) are all phrased per-room or
per-date; a building-wide aggregate was not asked for, and adding one risks
scope creep the RFP explicitly warns against (Section 5, Section 10).

## G7 - When a booking breaks more than one rule, which is reported?
**The first rule violated, in fixed BR-numeric order.** Every rule check
function walks BR1 to BR16 in that literal order for the operation being
performed and raises on the first failure. This is deterministic, easy to
document, and easy for front desk staff to reason about ("we always check
overlap first").

## G8 - Should a closed room appear in the utilisation report, with what available time?
**Yes, at 0.0%, available minutes still 720.** The room still physically
exists and still costs floor space whether or not it is open that day; the
lease decision needs to see it, not have it silently vanish.

## G9 - Does an amendment count as a new booking for BR7?
**No.** An amendment changes an existing booking; it does not add a fourth
booking to the day. The rule engine excludes the booking's own id when
counting a booker's active bookings during an amendment.

## G10 - Should the audit log record amendments as well as bookings/cancellations?
**Yes.** TC12 describes the audit log as "the record we would rely on in a
dispute." A dispute is at least as likely to be about a booking that was
changed as one that was made or cancelled, so every accepted and refused
attempt at all three operations is logged.

## G11 - When a room is renamed, what happens to bookings against the old name?
**Not applicable - room renaming is out of scope.** F13/F14 only add and
list rooms; no rename operation is requested anywhere in Section 4, so there
is no renaming feature to build and no orphaning risk to handle.

## G12 - Should free periods (F16) be reported inside a closure?
**No - a closed room simply has zero free periods for that date.** "Free"
implies bookable, and a closed room cannot be booked at all that day, so
listing open-looking gaps inside a closure would be misleading to the desk.
