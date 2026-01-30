"""
Test Data Validation Guardrails
Tests the validation rules to ensure they correctly block invalid inputs
"""
# -*- coding: utf-8 -*-
import sys
import io
sys.path.append('.')

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.agents.validator.validation_rules import (
    validate_email,
    validate_datetime,
    validate_event_times,
    validate_attendees,
    validate_slack_channel,
    validate_message_content,
    validate_calendar_event_input,
    validate_slack_message_input
)

print("Testing Data Validation Guardrails\n")

# Test 1: Email Validation
print("=" * 60)
print("Test 1: Email Validation")
print("=" * 60)

emails_valid = [
    "user@example.com",
    "john.doe@company.co.uk",
    "admin+test@domain.com"
]

emails_invalid = [
    "invalid",
    "user@",
    "@domain.com",
    "user..name@domain.com",
    ".user@domain.com"
]

for email in emails_valid:
    valid, error = validate_email(email)
    status = "[PASS]" if valid else f"[FAIL]: {error}"
    print(f"  {email:30} -> {status}")

for email in emails_invalid:
    valid, error = validate_email(email)
    status = "[PASS] (rejected)" if not valid else f"[FAIL] (should reject)"
    print(f"  {email:30} -> {status}")

# Test 2: Date/Time Validation
print("\n" + "=" * 60)
print("Test 2: Date/Time Validation")
print("=" * 60)

dates_valid = [
    "2026-02-05T18:00:00+05:30",
    "2026-12-31T23:59:00+05:30"
]

dates_invalid = [
    "2024-01-01T10:00:00+05:30",  # Past date
    "2030-01-01T10:00:00+05:30",  # Too far in future
    "invalid-date"
]

for date_str in dates_valid:
    valid, error = validate_datetime(date_str)
    status = "[PASS]" if valid else f"[FAIL]: {error}"
    print(f"  {date_str:35} -> {status}")

for date_str in dates_invalid:
    valid, error = validate_datetime(date_str)
    status = "[PASS] (rejected)" if not valid else f"[FAIL] (should reject)"
    print(f"  {date_str:35} -> {status}")

# Test 3: Event Time Validation
print("\n" + "=" * 60)
print("Test 3: Event Time Validation")
print("=" * 60)

# Valid: 1 hour meeting
valid, error = validate_event_times(
    "2026-02-05T18:00:00+05:30",
    "2026-02-05T19:00:00+05:30"
)
print(f"  1-hour meeting: {('[PASS]' if valid else f'[FAIL]: {error}')}")

# Invalid: End before start
valid, error = validate_event_times(
    "2026-02-05T19:00:00+05:30",
    "2026-02-05T18:00:00+05:30"
)
print(f"  End before start: {('[PASS] (rejected)' if not valid else '[FAIL] (should reject)')}")

# Invalid: Too short (5 minutes)
valid, error = validate_event_times(
    "2026-02-05T18:00:00+05:30",
    "2026-02-05T18:05:00+05:30"
)
print(f"  5-minute meeting: {('[PASS] (rejected)' if not valid else '[FAIL] (should reject)')}")

# Test 4: Attendee Validation
print("\n" + "=" * 60)
print("Test 4: Attendee Validation")
print("=" * 60)

# Valid
valid, error = validate_attendees(["john@company.com", "jane@company.com"])
print(f"  2 valid attendees: {('[PASS]' if valid else f'[FAIL]: {error}')}")

# Invalid: Duplicate
valid, error = validate_attendees(["john@company.com", "john@company.com"])
print(f"  Duplicate attendee: {('[PASS] (rejected)' if not valid else '[FAIL] (should reject)')}")

# Invalid: Invalid email
valid, error = validate_attendees(["invalid-email"])
print(f"  Invalid email in list: {('[PASS] (rejected)' if not valid else '[FAIL] (should reject)')}")

# Invalid: Too many
too_many = [f"user{i}@company.com" for i in range(150)]
valid, error = validate_attendees(too_many)
print(f"  150 attendees (max 100): {('[PASS] (rejected)' if not valid else '[FAIL] (should reject)')}")

# Test 5: Slack Channel Validation
print("\n" + "=" * 60)
print("Test 5: Slack Channel Validation")
print("=" * 60)

channels_valid = ["#general", "#social", "#team-updates"]
channels_invalid = ["general", "#", "#UPPERCASE", "#special!char"]

for channel in channels_valid:
    valid, error = validate_slack_channel(channel)
    status = "[PASS]" if valid else f"[FAIL]: {error}"
    print(f"  {channel:20} -> {status}")

for channel in channels_invalid:
    valid, error = validate_slack_channel(channel)
    status = "[PASS] (rejected)" if not valid else f"[FAIL] (should reject)"
    print(f"  {channel:20} -> {status}")

# Test 6: Message Content Validation
print("\n" + "=" * 60)
print("Test 6: Message Content Validation")
print("=" * 60)

# Valid message
valid, error = validate_message_content("Hello team, meeting at 3pm today")
print(f"  Normal message: {('[PASS]' if valid else f'[FAIL]: {error}')}")

# Invalid: Too long
long_msg = "A" * 5000
valid, error = validate_message_content(long_msg)
print(f"  5000 char message (max 4000): {('[PASS] (rejected)' if not valid else '[FAIL] (should reject)')}")

# Invalid: Contains API key
valid, error = validate_message_content("Here's my API_KEY: sk-abc123def456ghi789jkl")
print(f"  Message with API key: {('[PASS] (rejected)' if not valid else '[FAIL] (should reject)')}")

# Test 7: Full Calendar Event Validation
print("\n" + "=" * 60)
print("Test 7: Full Calendar Event Input")
print("=" * 60)

valid_event = {
    "title": "Team Meeting",
    "start_time": "2026-02-05T18:00:00+05:30",
    "end_time": "2026-02-05T19:00:00+05:30",
    "attendees": ["john@company.com", "jane@company.com"]
}

errors = validate_calendar_event_input(valid_event)
print(f"  Valid event: {('[PASS]' if not errors else f'[FAIL]: {errors}')}")

invalid_event_past = {
    "title": "Past Meeting",
    "start_time": "2024-01-01T10:00:00+05:30",
    "end_time": "2024-01-01T11:00:00+05:30"
}

errors = validate_calendar_event_input(invalid_event_past)
print(f"  Past date event: {('[PASS] (rejected)' if errors else '[FAIL] (should reject)')}")
if errors:
    print(f"    Errors: {errors[0]}")

# Test 8: Full Slack Message Validation
print("\n" + "=" * 60)
print("Test 8: Full Slack Message Input")
print("=" * 60)

valid_message = {
    "channel": "#general",
    "text": "Hello team!"
}

errors = validate_slack_message_input(valid_message)
print(f"  Valid message: {('[PASS]' if not errors else f'[FAIL]: {errors}')}")

invalid_message_channel = {
    "channel": "general",  # Missing #
    "text": "Hello"
}

errors = validate_slack_message_input(invalid_message_channel)
print(f"  Invalid channel format: {('[PASS] (rejected)' if errors else '[FAIL] (should reject)')}")
if errors:
    print(f"    Errors: {errors[0]}")

print("\n" + "=" * 60)
print("[SUCCESS] All tests completed!")
print("=" * 60)

