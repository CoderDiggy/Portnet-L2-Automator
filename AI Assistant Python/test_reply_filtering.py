"""
Test AI-Powered Smart Reply Filtering
Verify that the AI can intelligently recognize any type of simple reply or non-incident communication
"""

import asyncio
from app.services.email_monitor import EmailIncidentMonitor

async def test_ai_reply_filtering():
    """Test that AI correctly identifies various types of simple replies and conversational messages"""
    print("🧪 Testing AI-Powered Smart Reply Filtering...")
    print("🤖 Using intelligent AI classification to detect any type of simple reply")
    
    monitor = EmailIncidentMonitor()
    
    # Test cases - Diverse non-incident communications that should be filtered out
    non_incident_emails = [
        # Basic responses
        {
            "subject": "Re: System Update",
            "content": "yes",
            "description": "Single word affirmative"
        },
        {
            "subject": "Re: Container Issue", 
            "content": "no way",
            "description": "Casual negative response"
        },
        {
            "subject": "Hello",
            "content": "hey there, how's it going?",
            "description": "Casual greeting with question"
        },
        
        # Acknowledgments and confirmations
        {
            "subject": "Meeting Tomorrow",
            "content": "sounds perfect, I'll be there at 10am",
            "description": "Meeting confirmation"
        },
        {
            "subject": "RE: Budget Report",
            "content": "received, reviewing now",
            "description": "Document acknowledgment"
        },
        {
            "subject": "Training Schedule",
            "content": "noted, will attend the session on Friday",
            "description": "Training acknowledgment"
        },
        
        # Social and personal
        {
            "subject": "Weekend Plans",
            "content": "maybe we can grab coffee after work?",
            "description": "Social planning"
        },
        {
            "subject": "Happy Birthday!",
            "content": "hope you have a wonderful day and many happy returns!",
            "description": "Birthday wishes"
        },
        {
            "subject": "Congratulations",
            "content": "well done on the promotion, you deserve it!",
            "description": "Congratulatory message"
        },
        
        # Automated messages
        {
            "subject": "Delivery Notification",
            "content": "This is an automated message. Your package has been delivered to the front desk.",
            "description": "Automated delivery notification"
        },
        {
            "subject": "Out of Office Auto-Reply",
            "content": "Thank you for your email. I am currently out of the office with limited access to email. I will respond when I return next week.",
            "description": "Out of office auto-reply"
        },
        
        # Casual conversations
        {
            "subject": "Re: Lunch",
            "content": "actually, can we make it 1pm instead? something came up",
            "description": "Casual schedule change"
        },
        {
            "subject": "Weekend Update",
            "content": "had a great time at the beach, weather was perfect!",
            "description": "Personal update sharing"
        },
        {
            "subject": "Random thought",
            "content": "just wondering if you've seen the new cafeteria menu",
            "description": "Casual wondering/question"
        },
        
        # Questions without urgency
        {
            "subject": "Quick question",
            "content": "do you know what time the office closes on Friday?",
            "description": "Simple informational question"
        },
        
        # Expressions and reactions
        {
            "subject": "Amazing news!",
            "content": "wow, that's incredible! can't believe it finally happened",
            "description": "Excited reaction"
        },
        {
            "subject": "Re: Project Update",
            "content": "hmm, interesting approach. let me think about it over the weekend",
            "description": "Thoughtful response"
        },
        
        # Quoted text heavy emails
        {
            "subject": "Re: System Performance",
            "content": "> The system seems to be running smoothly now\n> All tests passed successfully\n> No issues detected\n\nGreat work team!",
            "description": "Mostly quoted text with brief comment"
        },
        
        # Creative/unusual simple replies
        {
            "subject": "Weird question",
            "content": "lol what even is this? 😂",
            "description": "Humorous confused reaction"
        },
        {
            "subject": "Re: Document",
            "content": "yep yep yep, all looks good to me",
            "description": "Repetitive casual approval"
        },
        {
            "subject": "Food order",
            "content": "definitely getting pizza, anyone else want some?",
            "description": "Food coordination message"
        }
    ]
    
    # Test cases - Real incidents that SHOULD be classified as incidents
    real_incident_emails = [
        {
            "subject": "URGENT: PORTNET Container Error CMAU123456",
            "content": "We have a critical issue with container CMAU123456 showing duplicate entries in PORTNET system. This is blocking vessel MV Pacific Star from completing discharge operations.",
            "description": "Real container system incident"
        },
        {
            "subject": "EDI Processing Failure - Immediate Attention Required",
            "content": "EDI message REF-IFT-0007 has been stuck in ERROR status for 2 hours. The ack_at field remains NULL and this is preventing cargo manifest processing for 3 vessels.",
            "description": "Real EDI system incident" 
        },
        {
            "subject": "System Down - Need Help",
            "content": "The vessel management system appears to be completely down. Getting VESSEL_ERR_4 on all operations. Multiple vessels affected including MV Lion City and MV Star Express.",
            "description": "Real system outage"
        }
    ]
    
    print(f"\n🚫 Testing {len(non_incident_emails)} Diverse Non-Incident Communications (should be filtered out):")
    non_incident_results = []
    
    for i, test_case in enumerate(non_incident_emails, 1):
        print(f"\n📧 Test {i}: {test_case['description']}")
        print(f"   Subject: {test_case['subject']}")
        print(f"   Content: {test_case['content'][:80]}{'...' if len(test_case['content']) > 80 else ''}")
        
        try:
            is_incident = await monitor.is_incident_email(
                test_case['subject'], 
                test_case['content']
            )
            
            expected = False  # These should NOT be incidents
            status = "✅ PASS" if is_incident == expected else "❌ FAIL"
            print(f"   AI Result: {is_incident} (Expected: {expected}) - {status}")
            
            non_incident_results.append({
                "test": i,
                "passed": is_incident == expected,
                "description": test_case['description']
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            non_incident_results.append({
                "test": i,
                "passed": False,
                "error": str(e)
            })
    
    print("\n✅ Testing Real Incident Emails (should be classified as incidents):")
    incident_results = []
    
    for i, test_case in enumerate(real_incident_emails, 1):
        print(f"\n🚨 Test {i}: {test_case['description']}")
        print(f"   Subject: {test_case['subject']}")
        print(f"   Content: {test_case['content'][:100]}...")
        
        try:
            is_incident = await monitor.is_incident_email(
                test_case['subject'], 
                test_case['content']
            )
            
            expected = True  # These SHOULD be incidents
            status = "✅ PASS" if is_incident == expected else "❌ FAIL"
            print(f"   Result: {is_incident} (Expected: {expected}) - {status}")
            
            incident_results.append({
                "test": i,
                "passed": is_incident == expected,
                "description": test_case['description']
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            incident_results.append({
                "test": i,
                "passed": False,
                "error": str(e)
            })
    
    # Summary
    non_incident_passed = sum(1 for r in non_incident_results if r.get('passed', False))
    incident_passed = sum(1 for r in incident_results if r.get('passed', False))
    
    print(f"\n" + "="*70)
    print("📊 AI-POWERED SMART REPLY FILTERING TEST RESULTS")
    print("="*70)
    print(f"🚫 Non-Incident Filtering: {non_incident_passed}/{len(non_incident_results)} passed")
    print(f"✅ Real Incident Detection: {incident_passed}/{len(incident_results)} passed")
    
    total_passed = non_incident_passed + incident_passed
    total_tests = len(non_incident_results) + len(incident_results)
    
    success_rate = (total_passed / total_tests) * 100
    print(f"🤖 AI Classification Accuracy: {total_passed}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 95:
        print("🎉 OUTSTANDING: AI filtering is exceptionally accurate!")
    elif success_rate >= 85:
        print("🚀 EXCELLENT: AI is effectively distinguishing reply types!")
    elif success_rate >= 75:
        print("👍 GOOD: AI classification working well with minor issues")
    else:
        print("⚠️  NEEDS TUNING: AI prompts may need adjustment")
    
    return {
        "non_incident_results": non_incident_results,
        "incident_results": incident_results,
        "success_rate": success_rate
    }

if __name__ == "__main__":
    # Run the AI-powered smart reply filtering test
    asyncio.run(test_ai_reply_filtering())