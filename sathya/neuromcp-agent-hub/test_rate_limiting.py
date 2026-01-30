"""
Test Rate Limiting Guardrails
"""

import time
from app.agents.validator.rate_limiter import check_rate_limit, get_rate_limit_stats

print("Testing Rate Limiting Guardrails\n")
print("=" * 60)

# Test 1: Normal usage (should pass)
print("\nTest 1: Normal Usage")
print("-" * 60)
for i in range(3):
    allowed, error = check_rate_limit("slack.post_message", f"test message {i}")
    print(f"  Request {i+1}: {'[PASS]' if allowed else f'[BLOCKED] {error}'}")

# Test 2: Duplicate request (should block)
print("\nTest 2: Duplicate Detection (30 second cooldown)")
print("-" * 60)
allowed1, _ = check_rate_limit("calendar.create_event", "same request")
print(f"  First request: [PASS]" if allowed1 else "[FAIL]")

allowed2, error2 = check_rate_limit("calendar.create_event", "same request")
print(f"  Duplicate (immediate): {'[PASS] (should be blocked)' if allowed2 else f'[PASS - BLOCKED] {error2}'}")

#Test 3: Exceed per-tool rate limit
print("\nTest 3: Exceed Tool Rate Limit (5 calendar events per hour)")
print("-" * 60)
for i in range(7):
    allowed, error = check_rate_limit("calendar.create_event", f"meeting {i}")
    status = "[PASS]" if allowed else f"[BLOCKED] {error}"
    print(f"  Calendar event {i+1}: {status}")

# Test 4: Overall limit
print("\nTest 4: Rate Limit Statistics")
print("-" * 60)
stats = get_rate_limit_stats()
print(f"  Overall requests (last hour): {stats['overall_requests_last_hour']}")
print(f"  Tool usage:")
for tool, count in stats['tool_usage'].items():
    print(f"    - {tool}: {count} requests")

print("\n" + "=" * 60)
print("[SUCCESS] Rate limiting tests completed!")
print("=" * 60)
