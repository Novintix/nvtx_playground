"""
Test script for LLM-based planner with message extraction
Run this to verify the Groq planner works correctly
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, 'strict')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.planner.agent import create_plan_with_groq
from app.agents.tool_discovery.agent import discover_tools

load_dotenv()


async def test_message_extraction():
    """Test various message extraction scenarios"""
    
    print("🧪 Testing LLM-based Message Extraction\n")
    print("=" * 60)
    
    # Get available tools
    tools = await discover_tools()
    print(f"✅ Discovered {len(tools)} tools\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Basic 'like X in #channel'",
            "request": "send like Hi team good morning in #social",
            "expected_text": "Hi team good morning",
            "expected_channel": "#social"
        },
        {
            "name": "Your original request",
            "request": "i need to send the details of todays agenda in slack group like Hi team good morning lets all meet me in lunch hour in #social channel",
            "expected_text": "Hi team good morning lets all meet me in lunch hour",
            "expected_channel": "#social"
        },
        {
            "name": "'saying X to #channel'",
            "request": "post message to #general saying Project update meeting at 3pm",
            "expected_text": "Project update meeting at 3pm",
            "expected_channel": "#general"
        },
        {
            "name": "Simple 'message #channel with X'",
            "request": "message #random with Hello everyone",
            "expected_text": "Hello everyone",
            "expected_channel": "#random"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['name']}")
        print(f"   Request: {test['request']}")
        
        try:
            # Check if GROQ_API_KEY exists
            if not os.getenv("GROQ_API_KEY"):
                print("   ❌ GROQ_API_KEY not found in environment")
                results.append({"test": test["name"], "status": "SKIPPED", "reason": "No API key"})
                continue
            
            # Generate plan
            plan = create_plan_with_groq(test['request'], tools, retries=2)
            
            # Convert to dict if Pydantic model
            if hasattr(plan, 'model_dump'):
                plan_dict = plan.model_dump()
            else:
                plan_dict = plan
            
            # Find Slack post step
            slack_step = None
            for step in plan_dict['steps']:
                if step.get('tool') == 'slack.post_message':
                    slack_step = step
                    break
            
            if not slack_step:
                print("   ❌ No slack.post_message step found in plan")
                results.append({"test": test["name"], "status": "FAIL", "reason": "No Slack step"})
                continue
            
            # Check extracted values
            actual_text = slack_step['input'].get('text', '')
            actual_channel = slack_step['input'].get('channel', '')
            
            print(f"   Extracted:")
            print(f"     Text: '{actual_text}'")
            print(f"     Channel: '{actual_channel}'")
            
            # Validate
            text_match = actual_text == test['expected_text']
            channel_match = actual_channel == test['expected_channel']
            
            if text_match and channel_match:
                print("   ✅ PASS")
                results.append({"test": test["name"], "status": "PASS"})
            else:
                print("   ❌ FAIL")
                if not text_match:
                    print(f"     Expected text: '{test['expected_text']}'")
                if not channel_match:
                    print(f"     Expected channel: '{test['expected_channel']}'")
                results.append({"test": test["name"], "status": "FAIL", "reason": "Mismatch"})
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({"test": test["name"], "status": "ERROR", "reason": str(e)})
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    skipped = sum(1 for r in results if r["status"] == "SKIPPED")
    
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    print(f"⚠️  Errors: {errors}/{len(test_cases)}")
    print(f"⏭️  Skipped: {skipped}/{len(test_cases)}")
    
    if passed == len(test_cases):
        print("\n🎉 All tests passed! LLM-based extraction is working perfectly.")
    elif skipped > 0:
        print("\n⚠️  Some tests were skipped. Check GROQ_API_KEY configuration.")
    else:
        print("\n⚠️  Some tests failed. Review the output above.")


if __name__ == "__main__":
    asyncio.run(test_message_extraction())
