# TRACEABILITY.md

Maps every requirement and rule due on Day 18 (F1-F16, BR1-BR16) to the
test(s) that cover it. Updated again at the end of the reporting/hardening
phase to add F17-F33 and every acceptance criterion.

## Functional requirements (F1-F16)

| Req | Description | Tests |
|---|---|---|
| F1 | Record a booking | tests/test_bookings.py::TestCreateBooking::test_F1_valid_booking_is_accepted |
| F2 | Refuse and name the broken rule | tests/test_bookings.py::TestCreateBooking::test_F2_refusal_names_the_rule (and every BR/F test below, all of which assert the exact rule id) |
| F3 | Cancel a booking by id | tests/test_bookings.py::TestCancel::test_F3_cancel_by_id |
| F4 | List all bookings for a date, ordered by room then start | tests/test_bookings.py::TestListAndRetrieve::test_F4_list_by_date_ordered_by_room_then_start |
| F5 | List all bookings for a room on a date | tests/test_bookings.py::TestListAndRetrieve::test_F5_list_by_room_and_date |
| F6 | Persist bookings across restarts | tests/test_storage.py::TestPersistence::test_F6_bookings_survive_reload |
| F33 | Booking ids unique, never reused after cancellation | tests/test_storage.py::TestPersistence::test_F33_ids_are_never_reused_after_cancellation |
| F7 | Report utilisation (duplicate of F17, see reporting phase) | tests/test_reports.py (reporting phase) |
| F8 | Report minutes/count per room (duplicate of F18) | tests/test_reports.py (reporting phase) |
| F9 | Retrieve a single booking by id | tests/test_bookings.py::TestListAndRetrieve::test_F9_get_booking_by_id, test_F9_get_missing_booking_raises |
| F10 | List bookings held by a booker on a date | tests/test_bookings.py::TestListAndRetrieve::test_F10_list_by_booker_and_date |
| F11 | Amend an existing booking | tests/test_amend_rooms.py::TestAmend::test_F11_amend_time |
| F12 | Re-apply every rule to an amendment | tests/test_amend_rooms.py::TestAmend::test_F12_amended_booking_reapplies_rules |
| F13 | Add a room | tests/test_amend_rooms.py::TestRoomAdmin::test_F13_add_room |
| F14 | List all rooms with capacities | tests/test_amend_rooms.py::TestRoomAdmin::test_F14_list_rooms |
| F15 | Mark a room closed for a date | tests/test_amend_rooms.py::TestRoomAdmin::test_F15_close_room |
| F16 | Show free periods of at least 15 minutes | tests/test_amend_rooms.py::TestRoomAdmin::test_F16_free_periods_exclude_bookings |

Gap: F6 test is listed here but written alongside the data-integrity suite
in the reporting/hardening phase (F6 depends on `storage.save`/`storage.load`,
exercised there with a fresh `BookingService` reload). F7/F8 are the same
figures as F17/F18 and are covered once, in `reports.py`, rather than twice.

## Business rules (BR1-BR16)

| Rule | Tests |
|---|---|
| BR1 | test_bookings.py::test_BR1_overlap_refused, test_BR1_touching_bookings_accepted; test_amend_rooms.py::test_F12_amended_booking_reapplies_rules |
| BR2 | test_bookings.py::test_BR2_below_minimum_refused, test_BR2_exactly_15_minutes_accepted, test_BR2_exactly_4_hours_accepted, test_BR2_above_maximum_refused |
| BR3 | test_bookings.py::test_BR3_not_on_quarter_hour_refused |
| BR4 | test_bookings.py::test_BR4_starts_before_opening_refused, test_BR4_ends_exactly_at_closing_accepted, test_BR4_ends_after_closing_refused |
| BR5 | test_bookings.py::test_BR5_over_capacity_refused, test_BR5_exactly_at_capacity_accepted; test_amend_rooms.py::test_amend_over_capacity_refused_BR5 |
| BR6 | test_bookings.py::test_BR6_past_booking_refused |
| BR7 | test_bookings.py::test_BR7_fourth_booking_same_day_refused |
| BR8 | test_bookings.py::test_BR8_cancel_within_cutoff_refused |
| BR9 | test_bookings.py::test_BR9_closed_room_refused |
| BR10 | test_amend_rooms.py::test_BR10_amendment_does_not_conflict_with_own_previous_slot |
| BR11 | test_amend_rooms.py::test_BR11_amend_within_cutoff_refused |
| BR12 | test_amend_rooms.py::test_BR12_duplicate_name_case_insensitive_refused |
| BR13 | test_bookings.py::test_BR13_bad_booker_id_refused |
| BR14 | test_amend_rooms.py::test_BR14_close_room_with_bookings_refused |
| BR15 | test_amend_rooms.py::test_BR15_capacity_zero_refused, test_BR15_capacity_51_refused |
| BR16 | test_amend_rooms.py::test_BR16_noop_amendment_refused |

## Structural input validation (F25-F28)

| Req | Tests |
|---|---|
| F25 | test_bookings.py::test_F25_missing_field_refused, test_F25_wrong_type_refused |
| F26 | test_bookings.py::test_F26_end_before_start_refused, test_F26_end_equals_start_refused |
| F27 | test_bookings.py::test_F27_nonexistent_date_refused |
| F28 | test_bookings.py::test_F28_unknown_room_refused |

## Status

F1-F5, F9-F16, BR1-BR7, BR9-BR16, F25-F28: **done, tested, green.**
F6, F8/F17/F18/F22-F24, BR8: **F6/F8 pending the persistence + reporting
suite; BR8 is tested above** (test_BR8_cancel_within_cutoff_refused).
Everything from F17 onward is scheduled for the next phase and will be
added to this table then, along with every AC1-AC42 status.
