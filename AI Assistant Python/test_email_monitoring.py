"""
Email Monitoring Test Script
Tests the automated incident ingestion feature without needing real email setup
"""

import asyncio
import json
from datetime import datetime
from app.services.email_monitor import EmailIncidentMonitor

async def test_email_classification():
    """Test email classification functionality"""
    print("🧪 Testing Email Classification...")
    
    monitor = EmailIncidentMonitor()
    
    # Test cases - maritime operations incident emails
    test_emails = [
        {
            "subject": "URGENT: PORTNET System Error - Container CMAU0000020",
            "content": "Hi team, we're seeing duplicate container information in PORTNET for container CMAU0000020. This is affecting vessel operations. Please investigate immediately.",
            "expected": True
        },
        {
            "subject": "VESSEL_ERR_4 - MV Lion City 07",
            "content": "Getting VESSEL_ERR_4 when trying to create vessel advice for MV Lion City 07. Error occurred at 14:30 today. Unable to process cargo manifest.",
            "expected": True
        },
        {
            "subject": "EDI Message Processing Failure",
            "content": "EDI message REF-IFT-0007 is stuck in ERROR status. The ack_at field is NULL and processing has stopped. This is blocking vessel operations.",
            "expected": True
        },
        {
            "subject": "Meeting Reminder",
            "content": "Don't forget about tomorrow's team meeting at 2 PM in the conference room.",
            "expected": False
        },
        {
            "subject": "Weekly Newsletter",
            "content": "Here's our weekly company newsletter with updates from HR and management.",
            "expected": False
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_emails, 1):
        print(f"\n📧 Test Case {i}: {test_case['subject'][:50]}...")
        
        try:
            is_incident = await monitor.is_incident_email(
                test_case['subject'], 
                test_case['content']
            )
            
            status = "✅ PASS" if is_incident == test_case['expected'] else "❌ FAIL"
            print(f"   Expected: {test_case['expected']}, Got: {is_incident} - {status}")
            
            results.append({
                "test": i,
                "passed": is_incident == test_case['expected'],
                "expected": test_case['expected'],
                "actual": is_incident
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({
                "test": i,
                "passed": False,
                "error": str(e)
            })
    
    # Summary
    passed = sum(1 for r in results if r.get('passed', False))
    total = len(results)
    print(f"\n📊 Classification Test Results: {passed}/{total} passed")
    
    return results

async def test_incident_creation():
    """Test incident creation from email data"""
    print("\n🧪 Testing Incident Creation...")
    
    monitor = EmailIncidentMonitor()
    
    # Test email data
    test_subject = "Critical: PORTNET Container Duplication Issue"
    test_content = """
    Hi Support Team,
    
    We have a critical issue with PORTNET where container CMAU0000020 is showing up twice in the system. 
    This is causing confusion for the vessel MV Lion City 07 operations.
    
    Error Details:
    - Container: CMAU0000020
    - Vessel: MV Lion City 07
    - Time: 2025-10-19 14:30 SGT
    - Impact: Vessel operations delayed
    
    Please investigate urgently.
    
    Best regards,
    Port Operations Team
    """
    test_sender = "operations@portauthority.com"
    test_date = datetime.now().isoformat()
    
    try:
        print("📧 Processing test email...")
        incident_data = await monitor.create_incident_from_email(
            test_subject, test_content, test_sender, test_date
        )
        
        print("✅ Incident created successfully!")
        print(f"   Incident ID: {incident_data['incident_id']}")
        print(f"   Title: {incident_data['extracted_data']['title']}")
        print(f"   Priority: {incident_data['extracted_data']['priority']}")
        print(f"   Category: {incident_data['extracted_data']['category']}")
        
        # Show AI analysis preview
        analysis = incident_data['ai_analysis'][:200]
        print(f"   AI Analysis: {analysis}...")
        
        return incident_data
        
    except Exception as e:
        print(f"❌ Error creating incident: {e}")
        return None

async def test_email_processing_simulation():
    """Simulate processing a real email"""
    print("\n🧪 Testing Full Email Processing Simulation...")
    
    monitor = EmailIncidentMonitor()
    
    # Simulate email message object
    class MockEmail:
        def __init__(self, subject, sender, content, date):
            self.subject = subject
            self.sender = sender
            self.content = content
            self.date = date
    
    # Test email
    mock_email = MockEmail(
        subject="System Alert: EDI Processing Failure - REF-IFT-0007",
        sender="alerts@maritime-systems.com",
        content="""
        ALERT: EDI Message Processing Failure
        
        Message ID: REF-IFT-0007
        Status: ERROR
        Timestamp: 2025-10-19 15:45:00
        
        Details:
        - Message stuck in processing queue
        - ack_at field is NULL
        - Affecting vessel manifest processing
        - Container operations impacted
        
        Immediate attention required.
        
        System: PORTNET EDI Gateway
        """,
        date="2025-10-19 15:45:00"
    )
    
    try:
        # Test classification
        print("1. 🔍 Classifying email...")
        is_incident = await monitor.is_incident_email(mock_email.subject, mock_email.content)
        print(f"   Classification: {'Incident' if is_incident else 'Not Incident'}")
        
        if is_incident:
            # Test incident creation
            print("2. 📝 Creating incident...")
            incident_data = await monitor.create_incident_from_email(
                mock_email.subject, mock_email.content, mock_email.sender, mock_email.date
            )
            
            print("3. 💾 Saving incident...")
            await monitor.save_email_incident(incident_data)
            
            print("✅ Full email processing completed!")
            print(f"   📧 Email from: {mock_email.sender}")
            print(f"   🎫 Incident ID: {incident_data['incident_id']}")
            print(f"   ⚡ Priority: {incident_data['extracted_data']['priority']}")
            
            return incident_data
        else:
            print("ℹ️  Email classified as non-incident - no further processing")
            return None
            
    except Exception as e:
        print(f"❌ Error in email processing: {e}")
        return None

async def run_all_tests():
    """Run comprehensive email monitoring tests"""
    print("🚀 Starting Email Monitoring Tests")
    print("=" * 50)
    
    try:
        # Test 1: Email Classification
        classification_results = await test_email_classification()
        
        # Test 2: Incident Creation  
        incident_data = await test_incident_creation()
        
        # Test 3: Full Processing Simulation
        processing_result = await test_email_processing_simulation()
        
        # Final Summary
        print("\n" + "=" * 50)
        print("📋 TEST SUMMARY")
        print("=" * 50)
        
        classification_passed = sum(1 for r in classification_results if r.get('passed', False))
        print(f"📊 Email Classification: {classification_passed}/{len(classification_results)} tests passed")
        print(f"📝 Incident Creation: {'✅ PASS' if incident_data else '❌ FAIL'}")
        print(f"🔄 Full Processing: {'✅ PASS' if processing_result else '❌ FAIL'}")
        
        print(f"\n🎯 Overall: {'✅ ALL SYSTEMS OPERATIONAL' if all([classification_passed >= 4, incident_data, processing_result]) else '⚠️  SOME ISSUES DETECTED'}")
        
    except Exception as e:
        print(f"❌ Critical test error: {e}")

if __name__ == "__main__":
    # Run tests
    asyncio.run(run_all_tests())