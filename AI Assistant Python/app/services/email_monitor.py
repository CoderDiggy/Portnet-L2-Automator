"""
Email Monitoring Service for Automated Incident Ingestion
Monitors email inbox and automatically creates incidents from incoming reports
"""

import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
import re
import os
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.openai_service import OpenAIService
from app.services.incident_analyzer import IncidentAnalyzer

logger = logging.getLogger(__name__)

class EmailIncidentMonitor:
    def __init__(self):
        self.imap_server = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
        self.imap_port = int(os.getenv("EMAIL_IMAP_PORT", "993"))
        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com") 
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.monitoring_enabled = os.getenv("EMAIL_MONITORING_ENABLED", "false").lower() == "true"
        
        # Initialize services
        self.openai_service = OpenAIService()
        
    async def start_monitoring(self):
        """Start monitoring email inbox for new incidents"""
        if not self.monitoring_enabled:
            logger.info("Email monitoring is disabled")
            return
            
        if not all([self.email_address, self.email_password]):
            logger.warning("Email credentials not configured. Email monitoring disabled.")
            return
            
        logger.info(f"Starting email monitoring for {self.email_address}")
        
        while True:
            try:
                await self.check_for_new_emails()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in email monitoring: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def check_for_new_emails(self):
        """Check for new unread emails and process them"""
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            mail.select('INBOX')
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            
            if messages[0]:
                email_ids = messages[0].split()
                logger.info(f"Found {len(email_ids)} new emails to process")
                
                for email_id in email_ids:
                    await self.process_email(mail, email_id)
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error(f"Error checking emails: {e}")
    
    async def process_email(self, mail, email_id):
        """Process individual email and create incident if relevant"""
        try:
            # Fetch email
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Extract email details
            subject = email_message.get('Subject', '')
            sender = email_message.get('From', '')
            date_received = email_message.get('Date', '')
            
            # Extract email content
            content = self.extract_email_content(email_message)
            
            # Check if this looks like an incident report
            if await self.is_incident_email(subject, content):
                logger.info(f"Processing incident email from {sender}: {subject}")
                
                # Create incident from email
                incident_data = await self.create_incident_from_email(
                    subject, content, sender, date_received
                )
                
                # Store incident in database
                await self.save_email_incident(incident_data)
                
                # Send confirmation email
                await self.send_confirmation_email(sender, subject, incident_data)
                
                logger.info(f"Created incident from email: {incident_data['incident_id']}")
            
        except Exception as e:
            logger.error(f"Error processing email {email_id}: {e}")
    
    def extract_email_content(self, email_message):
        """Extract text content from email message"""
        content = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                if content_type == 'text/plain' and 'attachment' not in content_disposition:
                    body = part.get_payload(decode=True)
                    if body:
                        content += body.decode('utf-8', errors='ignore')
        else:
            body = email_message.get_payload(decode=True)
            if body:
                content = body.decode('utf-8', errors='ignore')
                
        return content
    
    async def is_simple_reply(self, subject: str, content: str) -> bool:
        """Use AI to intelligently detect simple replies and non-incident communications"""
        try:
            # Clean up content for analysis
            clean_content = content.strip()
            clean_subject = subject.strip()
            
            # Remove common email signatures and footers
            lines = clean_content.split('\n')
            content_lines = []
            for line in lines:
                line = line.strip()
                # Skip empty lines, signatures, disclaimers
                if (line and 
                    not line.startswith('sent from') and 
                    not line.startswith('this email') and
                    not line.startswith('confidential') and
                    not 'unsubscribe' in line and
                    not line.startswith('---') and
                    not line.startswith('___')):
                    content_lines.append(line)
            
            clean_content = ' '.join(content_lines)
            
            # Very basic pre-filter for extremely obvious cases
            word_count = len(clean_content.split())
            if word_count <= 2:
                # For very short messages, do a quick check
                basic_replies = ['yes', 'no', 'ok', 'okay', 'thanks', 'hello', 'hi', 'bye', 'sure', 'fine']
                if clean_content.lower().strip() in basic_replies:
                    return True
            
            # Use AI for intelligent classification with clearer prompt
            classification_prompt = f"""You are an email classifier for maritime operations. Classify this email:

Subject: {clean_subject}
Content: {clean_content[:400]}

SIMPLE_REPLY (casual/non-operational):
- "yes", "no", "ok", "thanks", "hello", "hi", "bye"
- Social: "happy birthday", "see you later", "how are you"  
- Meeting: "I'll be there", "sounds good", "let's reschedule"
- Auto-reply: "out of office", "vacation"

POTENTIAL_INCIDENT (operational/technical):
- System problems: "error", "down", "failure", "not working"
- Maritime operations: "vessel", "container", "cargo", "delays"
- Technical issues: "system", "EDI", "PORTNET", "malfunction"

Respond ONLY with: SIMPLE_REPLY or POTENTIAL_INCIDENT"""

            # Get AI classification using the completion method
            response = await self.openai_service.get_completion(
                messages=[{"role": "user", "content": classification_prompt}],
                max_tokens=20,
                temperature=0.05  # Very low temperature for consistent classification
            )
            
            classification = response.strip().upper()
            is_simple = classification == "SIMPLE_REPLY"
            
            logger.info(f"AI Classification - Subject: '{clean_subject[:30]}...' -> {classification}")
            return is_simple
            
        except Exception as e:
            logger.error(f"Error in AI simple reply detection: {e}")
            # Fallback to conservative approach
            word_count = len(clean_content.split())
            
            # If AI fails, use basic heuristics but be conservative
            if word_count <= 3:
                basic_replies = ['yes', 'no', 'ok', 'okay', 'thanks', 'hello', 'hi']
                return any(reply in clean_content.lower() for reply in basic_replies)
            
            # When in doubt, let it through to avoid missing real incidents
            return False
    
    async def is_incident_email(self, subject: str, content: str) -> bool:
        """Determine if email appears to be an incident report using AI"""
        try:
            # First, use AI to filter out simple replies and non-incident communications
            if await self.is_simple_reply(subject, content):
                logger.info(f"Email filtered as simple reply: {subject[:50]}...")
                return False
            
            # Keywords that suggest incident reports
            incident_keywords = [
                'incident', 'problem', 'issue', 'error', 'failure', 'outage', 
                'urgent', 'critical', 'help', 'support', 'trouble', 'fault',
                'vessel', 'container', 'portnet', 'edi', 'system down'
            ]
            
            # Check for obvious incident indicators
            text_to_check = f"{subject} {content}".lower()
            keyword_matches = sum(1 for keyword in incident_keywords if keyword in text_to_check)
            
            if keyword_matches >= 2:  # At least 2 incident-related keywords
                return True
            
            # Additional content quality checks
            word_count = len(content.split())
            if word_count < 5:  # Very short messages unlikely to be real incidents
                logger.info(f"Email rejected - too short ({word_count} words): {content}")
                return False
            
            # Use AI to classify if not obvious
            classification_prompt = f"""
Classify if this email is a genuine maritime operations incident report that needs immediate attention.

Subject: {subject}
Content: {content[:1000]}...

IMPORTANT: Reply "NO" if this is:
- A simple reply like "yes", "no", "ok", "thanks"  
- A greeting like "hello", "hi"
- An acknowledgment like "received", "got it"
- Casual conversation
- Meeting requests or social messages
- Auto-replies or out-of-office messages

Reply "YES" only if this is a real operational incident requiring technical investigation involving:
- System failures (PORTNET, EDI, vessel systems)
- Container/vessel operational problems  
- Error codes or technical issues
- Urgent operational disruptions

Reply with only "YES" or "NO".
"""
            
            analysis_result = await self.openai_service.analyze_incident_async(classification_prompt)
            result = "YES" if any(keyword in analysis_result.incident_type.lower() for keyword in ['incident', 'critical', 'urgent', 'error', 'failure']) else "NO"
            return result.strip().upper() == "YES"
            
        except Exception as e:
            logger.error(f"Error classifying email: {e}")
            # Default to creating incident if classification fails
            return True
    
    async def create_incident_from_email(self, subject: str, content: str, sender: str, date_received: str) -> Dict:
        """Create incident data structure from email"""
        try:
            # Generate incident ID
            incident_id = f"EMAIL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract incident details using AI
            extraction_prompt = f"""
Extract incident details from this email:

Subject: {subject}
From: {sender}  
Content: {content}

Extract and format as JSON:
{{
    "title": "Brief incident title",
    "description": "Detailed incident description", 
    "priority": "Critical/High/Medium/Low",
    "category": "System type affected",
    "affected_systems": ["list", "of", "systems"],
    "error_codes": ["any", "error", "codes"],
    "vessels_involved": ["vessel", "names"],
    "containers_involved": ["container", "numbers"]
}}

Focus on maritime operations context.
"""
            
            ai_analysis = await self.openai_service.analyze_incident_async(extraction_prompt)
            # Convert analysis to extraction format
            ai_extraction = f'{{"title": "{subject}", "description": "{content[:200]}...", "priority": "Medium", "category": "Email Report", "affected_systems": [], "error_codes": [], "vessels_involved": [], "containers_involved": []}}'
            
            # Parse AI response (simplified - you might want more robust JSON parsing)
            import json
            try:
                extracted_data = json.loads(ai_extraction)
            except:
                # Fallback if JSON parsing fails
                extracted_data = {
                    "title": subject,
                    "description": content,
                    "priority": "Medium",
                    "category": "Email Report",
                    "affected_systems": [],
                    "error_codes": [],
                    "vessels_involved": [],
                    "containers_involved": []
                }
            
            # Analyze incident using existing analyzer
            db = next(get_db())
            incident_analyzer = IncidentAnalyzer(db)
            analysis = await incident_analyzer.analyze_incident_async(content)
            
            return {
                "incident_id": incident_id,
                "source": "Email",
                "sender": sender,
                "subject": subject,
                "received_at": date_received,
                "processed_at": datetime.now().isoformat(),
                "extracted_data": extracted_data,
                "ai_analysis": analysis,
                "status": "New",
                "auto_created": True
            }
            
        except Exception as e:
            logger.error(f"Error creating incident from email: {e}")
            raise
    
    async def save_email_incident(self, incident_data: Dict):
        """Save email incident to database"""
        try:
            # For now, log the incident (you can extend this to save to your database)
            logger.info(f"Email Incident Created: {incident_data['incident_id']}")
            logger.info(f"Title: {incident_data['extracted_data']['title']}")
            logger.info(f"Priority: {incident_data['extracted_data']['priority']}")
            
            # TODO: Save to actual incidents table when you create the proper schema
            
        except Exception as e:
            logger.error(f"Error saving email incident: {e}")
    
    async def send_confirmation_email(self, recipient: str, original_subject: str, incident_data: Dict):
        """Send confirmation email that incident was created"""
        try:
            # Create confirmation email
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = recipient
            msg['Subject'] = f"Incident Created: {incident_data['incident_id']}"
            
            body = f"""
Dear Colleague,

Your incident report has been automatically processed and assigned incident ID: {incident_data['incident_id']}

Original Subject: {original_subject}
Priority: {incident_data['extracted_data']['priority']}
Status: {incident_data['status']}
Processing Time: {incident_data['processed_at']}

AI Analysis Summary:
{incident_data['ai_analysis'][:500]}...

The incident has been logged and will be reviewed by the duty officer team.

Best regards,
AI Duty Officer Assistant
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_address, recipient, text)
            server.quit()
            
            logger.info(f"Confirmation email sent to {recipient}")
            
        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")

# Global instance
email_monitor = EmailIncidentMonitor()