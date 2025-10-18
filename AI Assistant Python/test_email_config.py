"""
Test Email Configuration
Quick script to verify email settings work
"""

import os
import asyncio
from app.services.email_monitor import EmailIncidentMonitor

async def test_email_connection():
    print("🧪 Testing Email Configuration...")
    
    # Check environment variables
    email_address = os.getenv("EMAIL_ADDRESS")
    email_enabled = os.getenv("EMAIL_MONITORING_ENABLED", "false").lower() == "true"
    
    print(f"📧 Email Address: {email_address}")
    print(f"🔧 Monitoring Enabled: {email_enabled}")
    
    if not email_enabled:
        print("❌ Email monitoring is disabled")
        print("   Set EMAIL_MONITORING_ENABLED=true in .env file")
        return False
    
    if not email_address or email_address == "your_email@gmail.com":
        print("❌ Email address not configured")
        print("   Set EMAIL_ADDRESS=your.actual.email@gmail.com in .env file")
        return False
    
    # Test email monitor initialization
    try:
        monitor = EmailIncidentMonitor()
        print("✅ Email monitor initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing email monitor: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_email_connection())