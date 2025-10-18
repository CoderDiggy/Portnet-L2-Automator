"""
Quick test for AI reply classification
"""
import asyncio
from app.services.email_monitor import EmailIncidentMonitor

async def quick_test():
    monitor = EmailIncidentMonitor()
    
    # Test the specific case that failed
    test_cases = [
        {"subject": "Re: Container Issue", "content": "no way", "expected": False, "desc": "Should be simple reply"},
        {"subject": "URGENT: Container Down", "content": "Container system showing errors", "expected": True, "desc": "Should be incident"},
        {"subject": "Hello", "content": "yes", "expected": False, "desc": "Simple yes"},
        {"subject": "System Problem", "content": "PORTNET is not responding", "expected": True, "desc": "Technical issue"},
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test['desc']}")
        print(f"Subject: {test['subject']}")
        print(f"Content: {test['content']}")
        
        try:
            result = await monitor.is_incident_email(test['subject'], test['content'])
            status = "✅ PASS" if result == test['expected'] else "❌ FAIL"
            print(f"Result: {result} (Expected: {test['expected']}) - {status}")
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())