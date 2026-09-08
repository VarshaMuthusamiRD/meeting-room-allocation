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

## Reporting and analysis (F17-F24)

| Req | Description | Tests |
|---|---|---|
| F17 | Room utilisation per date, 1 decimal place | tests/test_reports.py::test_F17_room_utilisation_matches_appendix_b |
| F18 | Total minutes and bookings per room, per date | tests/test_reports.py::test_F18_minutes_and_count_per_room |
| F19 | Seat utilisation for a date | tests/test_reports.py::test_F19_seat_utilisation_matches_appendix_b |
| F20 | Peak period for a date | tests/test_reports.py::test_F20_peak_period_matches_appendix_b |
| F21 | Bookings using fewer than half their room seats | tests/test_reports.py::test_F21_under_occupancy_empty_for_sample_data, test_F21_under_occupancy_detects_added_boardroom_booking |
| F22 | Room utilisation averaged across a date range | tests/test_reports.py::test_F22_range_average_utilisation |
| F23 | Per-booker bookings and minutes for a date | tests/test_reports.py::test_F23_per_booker_report |
| F24 | Empty minutes per room for a date | tests/test_reports.py::test_F24_empty_minutes_matches_appendix_b |

Every F17-F24 figure is asserted against the exact numeric values worked
out in Appendix B (booked minutes, percentages, peak hour, seat-minutes),
not just checked for "a number came back."

## Data integrity and resilience (F29-F33)

| Req | Description | Tests |
|---|---|---|
| F29 | Interrupted save cannot leave the file unreadable | tests/test_integrity.py::test_F29_failed_save_does_not_corrupt_existing_file, test_F29_no_stray_temp_files_after_successful_save |
| F30 | Corrupted/hand-edited file reported clearly on load | tests/test_integrity.py::test_F30_invalid_json_reported_clearly, test_F30_missing_required_keys_reported_clearly, test_F30_hand_edited_bad_field_type_reported_clearly |
| F31 | Dated backup before each save, 3 most recent retained | tests/test_integrity.py::test_F31_retains_three_most_recent_backups |
| F32 | Every accepted/refused attempt logged, append-only | tests/test_integrity.py::test_F32_accepted_booking_logged, test_F32_refused_booking_logged_with_rule_id, test_TC12_audit_log_is_append_only_across_runs |
| F33 | Booking ids unique, never reused after cancellation | tests/test_storage.py::test_F33_ids_are_never_reused_after_cancellation |
| F40 | Restore the data file from a chosen backup | tests/test_integrity.py::test_F40_restore_from_backup |

## Technical constraints (TC7-TC12)

| Constraint | Tests |
|---|---|
| TC7 | tests/test_config_clock.py::test_TC7_F39_fixed_now_makes_BR6_reproducible |
| TC9 | tests/test_config_clock.py::test_TC9_F35_opening_hours_come_from_config_not_code |
| TC10 | tests/test_performance.py (all 6 tests: list, report, range report, create, free periods, reload -- all under the 2-second budget on a 10,000-booking file) |
| TC12 | tests/test_integrity.py::test_TC12_audit_log_is_append_only_across_runs |

TC8 (format version carried in the data file) is exercised implicitly by
every `storage.save`/`storage.load` round trip (`format_version` is a
required key, validated in `_validate_structure`) and directly by
`version`/`check` CLI commands, covered manually in the Day-20 live
demonstration rather than by a dedicated unit test.

## Acceptance criteria (AC1-AC42)

| AC | Status | Where |
|---|---|---|
| AC1 | Pass | test_F1_valid_booking_is_accepted |
| AC2 | Pass | test_BR1_overlap_refused |
| AC3 | Pass | test_BR1_touching_bookings_accepted |
| AC4 | Pass | test_BR2_exactly_15_minutes_accepted, test_BR2_exactly_4_hours_accepted |
| AC5 | Pass | test_BR2_below_minimum_refused, test_BR2_above_maximum_refused |
| AC6 | Pass | test_BR3_not_on_quarter_hour_refused |
| AC7 | Pass | test_BR4_ends_exactly_at_closing_accepted, test_BR4_ends_after_closing_refused |
| AC8 | Pass | test_BR5_over_capacity_refused |
| AC9 | Pass | test_BR7_fourth_booking_same_day_refused |
| AC10 | Pass | test_BR8_cancel_within_cutoff_refused |
| AC11 | Pass | test_AC11_cancelled_slot_becomes_available |
| AC12 | Pass | test_F6_bookings_survive_reload |
| AC13 | Pass | test_F17_room_utilisation_matches_appendix_b (Boardroom 100.0, Focus 2 0.0) |
| AC14 | Pass | test_F17_room_utilisation_matches_appendix_b (matches Appendix B exactly) |
| AC15 | Pass | test_F2_refusal_names_the_rule, and every BR/F test asserts an exact rule id |
| AC16 | Pass | test_F12_amended_booking_reapplies_rules |
| AC17 | Pass | test_BR10_amendment_does_not_conflict_with_own_previous_slot |
| AC18 | Pass | test_BR11_amend_within_cutoff_refused |
| AC19 | Pass | test_BR16_noop_amendment_refused |
| AC20 | Pass | test_BR9_closed_room_refused |
| AC21 | Pass | test_BR14_close_room_with_bookings_refused |
| AC22 | Pass | test_BR12_duplicate_name_case_insensitive_refused |
| AC23 | Pass | test_BR13_bad_booker_id_refused |
| AC24 | Pass | test_BR15_capacity_zero_refused, test_BR15_capacity_51_refused |
| AC25 | Pass | test_F26_end_equals_start_refused |
| AC26 | Pass | test_F26_end_before_start_refused |
| AC27 | Pass | test_F27_nonexistent_date_refused |
| AC28 | Pass | test_F28_unknown_room_refused |
| AC29 | Pass | test_F16_free_periods_exclude_bookings |
| AC30 | Pass | test_F19_seat_utilisation_matches_appendix_b |
| AC31 | Pass | test_F20_peak_period_matches_appendix_b |
| AC32 | Pass | test_F21_under_occupancy_detects_added_boardroom_booking |
| AC33 | Pass | test_F24_empty_minutes_matches_appendix_b |
| AC34 | Pass | test_F33_ids_are_never_reused_after_cancellation |
| AC35 | Pass | test_F32_refused_booking_logged_with_rule_id |
| AC36 | Pass | test_TC12_audit_log_is_append_only_across_runs |
| AC37 | Pass | test_F30_invalid_json_reported_clearly, test_F30_missing_required_keys_reported_clearly |
| AC38 | Pass | test_F31_retains_three_most_recent_backups, test_F40_restore_from_backup |
| AC39 | Pass | test_TC9_F35_opening_hours_come_from_config_not_code |
| AC40 | Pass | test_TC7_F39_fixed_now_makes_BR6_reproducible |
| AC41 | Pass | tests/test_performance.py (all TC10 tests) |
| AC42 | Pass | test_F38_usage_lists_every_operation |

## Operability (F34-F40)

| Req | Description | Tests |
|---|---|---|
| F34 | Startup self-check: data file present, readable, valid | tests/test_operability.py::test_F34_check_on_fresh_data_dir_succeeds, test_F34_check_on_corrupted_file_fails_clearly |
| F35 | Opening hours/limits read from config, not hardcoded | tests/test_config_clock.py::test_TC9_F35_opening_hours_come_from_config_not_code |
| F36 | Report software and data format version | tests/test_operability.py::test_F36_version_reports_software_and_format_version |
| F37 | Success/failure exit code a script can act on | tests/test_operability.py::test_F37_success_exit_code_is_zero, test_F37_failure_exit_code_is_nonzero |
| F38 | Usage message lists every operation and its arguments | tests/test_operability.py::test_F38_usage_lists_every_operation |
| F39 | Current date/time accepted as an input (--now) | tests/test_config_clock.py::test_TC7_F39_fixed_now_makes_BR6_reproducible; tests/test_operability.py::test_F39_now_override_changes_reported_refusal |
| F40 | Restore the data file from a chosen backup | tests/test_integrity.py::test_F40_restore_from_backup; tests/test_operability.py::test_F40_restore_backup_via_cli |

## Should-have requirements (F41-F44)

| Req | Description | Tests |
|---|---|---|
| F41 | Suggest the smallest free room that fits the attendees | tests/test_should_haves.py::TestSuggestRoom (7 tests: smallest fit, skips too-small, skips occupied, skips closed, returns None when nothing fits, F26/BR5 boundary refusals) |
| F42 | Warn, but still allow, a booking under half the room's seats | tests/test_should_haves.py::TestUnderOccupancyWarning (4 tests: warns below half, no warning at exactly half, no warning above half, booking still accepted) |
| F43 | Text timeline of a day, one line per room | tests/test_should_haves.py::TestDayTimeline (3 tests: one row per room, occupied cells marked, closed rooms flagged) |
| F44 | Move a booking to another room, keeping its id | tests/test_should_haves.py::TestMoveBooking (5 tests: id kept, old slot freed, same-room move refused as BR16 no-op, over-capacity move refused as BR5, occupied-room move refused as BR1) |

F44 is implemented as a thin wrapper around the existing `amend_booking`,
so it inherits every rule check (BR1/BR5/BR10/BR11/BR16) rather than
duplicating logic -- the boundary tests above confirm that reuse actually
works end to end, not just that a new code path exists.

## Status

**All 40 must-have requirements (F1-F40), all 16 business rules
(BR1-BR16), all technical constraints TC7/TC9/TC10/TC12, all 42 acceptance
criteria (AC1-AC42), and all four should-have requirements (F41-F44) are
done, tested, and passing (120 tests, all green).** F45-F48 (could-have)
were deliberately not attempted -- see LIMITATIONS.md for the reasoning.
The live demonstration against the Appendix A sample data (rule-named
refusals for BR1 and BR7, every F17-F24 report figure, and a live
suggest-room/book/timeline/move walkthrough) is recorded in
BOARDROOM_FINDING.md and HANDOVER.md.
