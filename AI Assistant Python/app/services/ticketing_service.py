"""
Ticketing and Escalation Service
Integrates with ticketing systems like Jira and ServiceNow to auto-generate tickets and escalation summaries
"""

import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class TicketingService:
    def __init__(self):
        # Jira Configuration
        self.jira_url = os.getenv("JIRA_URL")
        self.jira_username = os.getenv("JIRA_USERNAME")
        self.jira_token = os.getenv("JIRA_TOKEN")
        self.jira_project_key = os.getenv("JIRA_PROJECT_KEY", "OPS")
        
        # ServiceNow Configuration
        self.servicenow_url = os.getenv("SERVICENOW_URL")
        self.servicenow_username = os.getenv("SERVICENOW_USERNAME")
        self.servicenow_password = os.getenv("SERVICENOW_PASSWORD")
        
        # Ticketing settings
        self.auto_create_tickets = os.getenv("AUTO_CREATE_TICKETS", "false").lower() == "true"
        self.default_ticketing_system = os.getenv("DEFAULT_TICKETING_SYSTEM", "jira").lower()
        
        self.openai_service = OpenAIService()
        
    async def create_ticket_from_incident(self, incident_data: Dict, analysis: str) -> Dict:
        """Create a ticket in the configured ticketing system"""
        try:
            # Generate escalation summary
            escalation_summary = await self.generate_escalation_summary(incident_data, analysis)
            
            # Determine priority and urgency
            ticket_priority = await self.determine_ticket_priority(incident_data, analysis)
            
            # Create ticket based on configured system
            if self.default_ticketing_system == "jira":
                result = await self.create_jira_ticket(incident_data, analysis, escalation_summary, ticket_priority)
            elif self.default_ticketing_system == "servicenow":
                result = await self.create_servicenow_ticket(incident_data, analysis, escalation_summary, ticket_priority)
            else:
                result = await self.create_generic_ticket(incident_data, analysis, escalation_summary, ticket_priority)
            
            logger.info(f"Ticket created: {result.get('ticket_id', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            return {"error": str(e), "ticket_created": False}
    
    async def generate_escalation_summary(self, incident_data: Dict, analysis: str) -> Dict:
        """Generate non-technical escalation summary for management"""
        try:
            escalation_prompt = f"""
Create a non-technical escalation summary for management based on this incident:

Incident Details:
{json.dumps(incident_data, indent=2)}

Technical Analysis:
{analysis}

Generate a JSON response with:
{{
    "executive_summary": "Brief business impact summary (2-3 sentences)",
    "business_impact": "Specific business impact and affected operations",
    "urgency_justification": "Why this needs immediate attention",
    "resource_requirements": "What resources/teams are needed",
    "estimated_resolution_time": "Estimated time to resolve",
    "stakeholder_notification": ["List", "of", "stakeholders", "to", "notify"],
    "escalation_level": "Low/Medium/High/Critical"
}}

Focus on business impact, not technical details. Use language suitable for C-level executives.
"""
            
            result = await self.openai_service.get_analysis_async(escalation_prompt)
            
            try:
                escalation_data = json.loads(result)
                return escalation_data
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "executive_summary": "Maritime operations incident requiring attention",
                    "business_impact": "Potential disruption to port operations",
                    "urgency_justification": "System reliability concern",
                    "resource_requirements": "Technical team assessment needed",
                    "estimated_resolution_time": "2-4 hours",
                    "stakeholder_notification": ["Operations Manager", "IT Manager"],
                    "escalation_level": "Medium"
                }
                
        except Exception as e:
            logger.error(f"Error generating escalation summary: {e}")
            return {"error": str(e)}
    
    async def determine_ticket_priority(self, incident_data: Dict, analysis: str) -> str:
        """Determine appropriate ticket priority based on AI analysis"""
        try:
            priority_prompt = f"""
Determine the ticket priority for this maritime operations incident:

Incident: {json.dumps(incident_data, indent=2)}
Analysis: {analysis}

Consider:
- System criticality (PORTNET, vessel operations, container tracking)
- Business impact (revenue, compliance, safety)
- Number of users affected
- Time sensitivity

Reply with only one word: Critical, High, Medium, or Low
"""
            
            priority = await self.openai_service.get_analysis_async(priority_prompt)
            priority = priority.strip().title()
            
            if priority not in ["Critical", "High", "Medium", "Low"]:
                priority = "Medium"  # Default fallback
                
            return priority
            
        except Exception as e:
            logger.error(f"Error determining priority: {e}")
            return "Medium"
    
    async def create_jira_ticket(self, incident_data: Dict, analysis: str, escalation: Dict, priority: str) -> Dict:
        """Create ticket in Jira"""
        try:
            if not all([self.jira_url, self.jira_username, self.jira_token]):
                return {"error": "Jira credentials not configured", "ticket_created": False}
            
            # Prepare Jira ticket data
            summary = f"Maritime Operations Incident: {incident_data.get('description', 'Unknown')[:100]}..."
            
            description = f"""
*Incident ID:* {incident_data.get('id', 'N/A')}
*Source:* {incident_data.get('source', 'Manual')}
*Reported:* {incident_data.get('reported_at', datetime.now().isoformat())}

*Executive Summary:*
{escalation.get('executive_summary', 'N/A')}

*Business Impact:*
{escalation.get('business_impact', 'N/A')}

*Technical Analysis:*
{analysis[:1000]}...

*Resource Requirements:*
{escalation.get('resource_requirements', 'N/A')}

*Estimated Resolution Time:*
{escalation.get('estimated_resolution_time', 'N/A')}

*Stakeholders to Notify:*
{', '.join(escalation.get('stakeholder_notification', []))}
"""
            
            # Map priority to Jira priority IDs (adjust based on your Jira setup)
            priority_mapping = {
                "Critical": "1",  # Highest
                "High": "2",      # High  
                "Medium": "3",    # Medium
                "Low": "4"        # Low
            }
            
            ticket_data = {
                "fields": {
                    "project": {"key": self.jira_project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": "Task"},  # Adjust based on your setup
                    "priority": {"id": priority_mapping.get(priority, "3")},
                    "labels": ["maritime-operations", "ai-generated", "incident"]
                }
            }
            
            # Create Jira ticket
            headers = {
                "Content-Type": "application/json",
            }
            
            response = requests.post(
                f"{self.jira_url}/rest/api/2/issue/",
                json=ticket_data,
                headers=headers,
                auth=(self.jira_username, self.jira_token),
                timeout=30
            )
            
            if response.status_code == 201:
                ticket_info = response.json()
                ticket_key = ticket_info["key"]
                ticket_url = f"{self.jira_url}/browse/{ticket_key}"
                
                return {
                    "ticket_created": True,
                    "system": "Jira",
                    "ticket_id": ticket_key,
                    "ticket_url": ticket_url,
                    "priority": priority,
                    "escalation_summary": escalation
                }
            else:
                logger.error(f"Jira API error: {response.status_code} - {response.text}")
                return {"error": f"Jira API error: {response.status_code}", "ticket_created": False}
                
        except Exception as e:
            logger.error(f"Error creating Jira ticket: {e}")
            return {"error": str(e), "ticket_created": False}
    
    async def create_servicenow_ticket(self, incident_data: Dict, analysis: str, escalation: Dict, priority: str) -> Dict:
        """Create ticket in ServiceNow"""
        try:
            if not all([self.servicenow_url, self.servicenow_username, self.servicenow_password]):
                return {"error": "ServiceNow credentials not configured", "ticket_created": False}
            
            # Prepare ServiceNow incident data
            short_description = f"Maritime Operations: {incident_data.get('description', 'Incident')[:100]}"
            
            description = f"""
Incident ID: {incident_data.get('id', 'N/A')}
Source: {incident_data.get('source', 'Manual')}
Reported: {incident_data.get('reported_at', datetime.now().isoformat())}

Executive Summary:
{escalation.get('executive_summary', 'N/A')}

Business Impact:
{escalation.get('business_impact', 'N/A')}

Technical Analysis:
{analysis[:1000]}

Resource Requirements:
{escalation.get('resource_requirements', 'N/A')}
"""
            
            # Map priority to ServiceNow values
            priority_mapping = {
                "Critical": "1",
                "High": "2", 
                "Medium": "3",
                "Low": "4"
            }
            
            # Map urgency based on escalation level
            urgency_mapping = {
                "Critical": "1",
                "High": "2",
                "Medium": "3", 
                "Low": "4"
            }
            
            urgency = urgency_mapping.get(escalation.get('escalation_level', 'Medium'), "3")
            
            incident_payload = {
                "short_description": short_description,
                "description": description,
                "priority": priority_mapping.get(priority, "3"),
                "urgency": urgency,
                "category": "Maritime Operations",
                "subcategory": "System Incident",
                "caller_id": self.servicenow_username,
                "assignment_group": "Maritime IT Support"  # Adjust based on your setup
            }
            
            # Create ServiceNow incident
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = requests.post(
                f"{self.servicenow_url}/api/now/table/incident",
                json=incident_payload,
                headers=headers,
                auth=(self.servicenow_username, self.servicenow_password),
                timeout=30
            )
            
            if response.status_code == 201:
                ticket_info = response.json()["result"]
                ticket_number = ticket_info["number"]
                ticket_sys_id = ticket_info["sys_id"]
                ticket_url = f"{self.servicenow_url}/nav_to.do?uri=%2Fincident.do%3Fsys_id%3D{ticket_sys_id}"
                
                return {
                    "ticket_created": True,
                    "system": "ServiceNow",
                    "ticket_id": ticket_number,
                    "ticket_url": ticket_url,
                    "priority": priority,
                    "escalation_summary": escalation
                }
            else:
                logger.error(f"ServiceNow API error: {response.status_code} - {response.text}")
                return {"error": f"ServiceNow API error: {response.status_code}", "ticket_created": False}
                
        except Exception as e:
            logger.error(f"Error creating ServiceNow ticket: {e}")
            return {"error": str(e), "ticket_created": False}
    
    async def create_generic_ticket(self, incident_data: Dict, analysis: str, escalation: Dict, priority: str) -> Dict:
        """Create a generic ticket structure when external systems aren't configured"""
        try:
            ticket_id = f"INC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            generic_ticket = {
                "ticket_created": True,
                "system": "Internal",
                "ticket_id": ticket_id,
                "priority": priority,
                "escalation_summary": escalation,
                "created_at": datetime.now().isoformat(),
                "details": {
                    "incident_data": incident_data,
                    "analysis": analysis,
                    "status": "Open"
                }
            }
            
            # Log the ticket (in production, you'd save this to database)
            logger.info(f"Generic ticket created: {ticket_id}")
            logger.info(f"Priority: {priority}")
            logger.info(f"Executive Summary: {escalation.get('executive_summary')}")
            
            return generic_ticket
            
        except Exception as e:
            logger.error(f"Error creating generic ticket: {e}")
            return {"error": str(e), "ticket_created": False}
    
    async def send_escalation_notifications(self, ticket_data: Dict, escalation: Dict):
        """Send notifications to stakeholders about escalated incidents"""
        try:
            stakeholders = escalation.get('stakeholder_notification', [])
            escalation_level = escalation.get('escalation_level', 'Medium')
            
            if escalation_level in ['High', 'Critical']:
                # Send immediate notifications for high-priority incidents
                notification_message = f"""
URGENT: Maritime Operations Incident Escalation

Ticket: {ticket_data.get('ticket_id')}
Priority: {ticket_data.get('priority')}
System: {ticket_data.get('system')}

Executive Summary:
{escalation.get('executive_summary')}

Business Impact:
{escalation.get('business_impact')}

Estimated Resolution: {escalation.get('estimated_resolution_time')}

Action Required: Please review and coordinate response.

Ticket URL: {ticket_data.get('ticket_url', 'N/A')}
"""
                
                logger.info(f"Escalation notification prepared for: {', '.join(stakeholders)}")
                logger.info(f"Notification message: {notification_message[:200]}...")
                
                # In production, you'd integrate with your notification system
                # (email, SMS, Slack, Teams, etc.)
                
            return {"notifications_sent": True, "recipients": stakeholders}
            
        except Exception as e:
            logger.error(f"Error sending escalation notifications: {e}")
            return {"error": str(e), "notifications_sent": False}

# Global instance
ticketing_service = TicketingService()