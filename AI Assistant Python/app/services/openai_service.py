import httpx
import json
import logging
from typing import Optional, List
import os
from ..models.schemas import IncidentAnalysis, TrainingDataResponse, KnowledgeBaseResponse
from ..models.database import TrainingData, KnowledgeBase

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.deployment_id = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        logger.info(f"Azure OpenAI Configuration - API Key: {'***' + self.api_key[-4:] if self.api_key else 'None'}")
        logger.info(f"Azure OpenAI Configuration - Endpoint: {self.endpoint}")
        logger.info(f"Azure OpenAI Configuration - Deployment ID: {self.deployment_id}")
        logger.info(f"Azure OpenAI Configuration - API Version: {self.api_version}")
        
        if not self.api_key or "PUT-YOUR-" in self.api_key or not self.endpoint or not self.deployment_id:
            logger.warning("Azure OpenAI configuration incomplete. AI analysis will use fallback mode.")
            logger.warning(f"Missing: API Key={not bool(self.api_key)}, Endpoint={not bool(self.endpoint)}, Deployment={not bool(self.deployment_id)}")
            self.configured = False
        else:
            logger.info("Azure OpenAI configuration complete. AI analysis enabled.")
            self.configured = True
    
    async def analyze_image_async(self, image_base64: str, incident_description: str = "") -> str:
        """Analyze image using Azure OpenAI Vision API"""
        if not self.configured:
            logger.warning("Using fallback image analysis - Azure OpenAI not configured")
            return "[Image Analysis: Visual analysis shows maritime incident documentation. Azure OpenAI Vision would extract detailed incident information including equipment damage, operational issues, safety concerns, and environmental conditions visible in the image.]"
        
        try:
            prompt = f"""You are an expert maritime operations analyst. Analyze this incident image and provide detailed observations.

            Context: {incident_description if incident_description else 'Maritime incident analysis'}
            
            Please identify and describe:
            1. Equipment or infrastructure visible
            2. Any visible damage, issues, or anomalies
            3. Safety concerns or hazards
            4. Environmental conditions
            5. Personnel or operational context
            6. Specific maritime/port operations details
            
            Provide a concise but detailed analysis focusing on incident-relevant details."""

            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Use Azure OpenAI endpoint with vision capabilities
            azure_url = f"{self.endpoint}/openai/deployments/{self.deployment_id}/chat/completions?api-version={self.api_version}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(azure_url, json=request_body, headers=headers, timeout=30.0)
                
                if response.is_success:
                    response_data = response.json()
                    vision_analysis = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    logger.info(f"Vision analysis completed successfully")
                    return vision_analysis
                else:
                    logger.error(f"Vision API error: {response.status_code} - {response.text}")
                    return "[Image analysis failed - API error]"
                    
        except Exception as ex:
            logger.error(f"Error in vision analysis: {ex}")
            return "[Image analysis encountered an error]"

    async def analyze_incident_async(self, description: str, training_data: List[TrainingData] = None, knowledge_data: List[KnowledgeBase] = None) -> IncidentAnalysis:
        """Analyze incident using AI with training data and knowledge base context"""
        
        # If configuration incomplete, use fallback
        if not self.configured:
            logger.warning("Using fallback analysis - Azure OpenAI not configured properly")
            return self._create_fallback_analysis(description)
        
        logger.info("Using Azure OpenAI for incident analysis")
        
        try:
            prompt = self._create_analysis_prompt(description, training_data, knowledge_data)
            
            request_body = {
                "messages": [
                    {"role": "system", "content": "You are an expert maritime operations analyst for PORTNET®."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Use Azure OpenAI endpoint
            azure_url = f"{self.endpoint}/openai/deployments/{self.deployment_id}/chat/completions?api-version={self.api_version}"
            logger.info(f"Making request to Azure OpenAI: {azure_url}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(azure_url, json=request_body, headers=headers, timeout=30.0)
                
                if response.is_success:
                    response_data = response.json()
                    ai_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    logger.info(f"OpenAI Response: {ai_content}")
                    return self._parse_analysis_response(ai_content)
                else:
                    error_content = response.text
                    logger.error(f"OpenAI API error: {response.status_code} - {error_content}")
                    return self._create_fallback_analysis(description)
                    
        except Exception as ex:
            logger.error(f"Error calling OpenAI API: {ex}")
            return self._create_fallback_analysis(description)
    
    def _create_analysis_prompt(self, description: str, training_examples: List[TrainingData] = None, knowledge_entries: List[KnowledgeBase] = None) -> str:
        """Create analysis prompt with training data and knowledge context"""
        
        training_section = ""
        if training_examples:
            training_section = "\nTRAINING EXAMPLES (Use these as reference for similar incidents):\n"
            for i, example in enumerate(training_examples):
                training_section += f"""
Example {i + 1}:
Description: {example.incident_description}
Type: {example.expected_incident_type}
Pattern: {example.expected_pattern_match}
Root Cause: {example.expected_root_cause}
Impact: {example.expected_impact}
Urgency: {example.expected_urgency}
Affected Systems: {', '.join(example.expected_affected_systems)}
---"""
        
        knowledge_section = ""
        if knowledge_entries:
            knowledge_section = "\nKNOWLEDGE BASE (Use this information to enhance your analysis):\n"
            for i, entry in enumerate(knowledge_entries):
                knowledge_section += f"""
Knowledge {i + 1} - {entry.title} ({entry.type}):
{entry.content[:500]}{'...' if len(entry.content) > 500 else ''}
Category: {entry.category}
Keywords: {entry.keywords}
---"""
        
        prompt = f"""Analyze this maritime/port operations incident and provide a structured analysis:

INCIDENT DESCRIPTION: {description}
{training_section}
{knowledge_section}

Please provide your analysis in the following JSON format:
{{
    "incident_type": "Brief categorization (e.g., Container Management, Vessel Operations, EDI Processing, etc.)",
    "pattern_match": "What pattern or category this incident matches",
    "root_cause": "Likely root cause based on the description and knowledge base",
    "impact": "Potential impact on operations",
    "urgency": "Low/Medium/High/Critical based on operational impact",
    "affected_systems": ["List of systems that might be affected"]
}}

Focus on maritime operations context including PORTNET®, container management, vessel operations, EDI messaging, terminal operations, and billing systems."""
        
        return prompt
    
    def _parse_analysis_response(self, ai_response: str) -> IncidentAnalysis:
        """Parse AI response into IncidentAnalysis object"""
        try:
            # Try to extract JSON from response
            start = ai_response.find('{')
            end = ai_response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = ai_response[start:end]
                data = json.loads(json_str)
                
                return IncidentAnalysis(
                    incident_type=data.get("incident_type", "System Issue"),
                    pattern_match=data.get("pattern_match", "General incident"),
                    root_cause=data.get("root_cause", "Under investigation"),
                    impact=data.get("impact", "Operational impact being assessed"),
                    urgency=data.get("urgency", "Medium"),
                    affected_systems=data.get("affected_systems", [])
                )
        except Exception as ex:
            logger.error(f"Error parsing AI response: {ex}")
        
        # Fallback parsing if JSON fails
        return self._create_fallback_analysis_from_text(ai_response)
    
    def _create_fallback_analysis(self, description: str) -> IncidentAnalysis:
        """Create fallback analysis when AI is not available"""
        description_lower = description.lower()
        
        # Simple pattern matching
        incident_type = "System Issue"
        affected_systems = []
        urgency = "Medium"
        
        # Pattern matching logic
        if any(word in description_lower for word in ["container", "cmau", "gesu", "trlu"]):
            incident_type = "Container Management"
            affected_systems = ["Container Management System", "PORTNET®"]
        elif any(word in description_lower for word in ["vessel", "ship", "mv "]):
            incident_type = "Vessel Operations"
            affected_systems = ["Vessel Management System", "PORTNET®"]
            urgency = "High"
        elif any(word in description_lower for word in ["edi", "message", "ref-ift"]):
            incident_type = "EDI Processing"
            affected_systems = ["EDI System", "Message Processing"]
        elif any(word in description_lower for word in ["gate", "truck", "access"]):
            incident_type = "Terminal Operations"
            affected_systems = ["Gate System", "Access Control"]
        elif any(word in description_lower for word in ["billing", "invoice", "charge"]):
            incident_type = "Financial Operations"
            affected_systems = ["Billing System", "Financial Module"]
        
        # Urgency assessment
        if any(word in description_lower for word in ["critical", "urgent", "error", "failure", "stuck"]):
            urgency = "High"
        elif any(word in description_lower for word in ["minor", "cosmetic"]):
            urgency = "Low"
        
        # Enhanced root cause analysis based on patterns
        root_cause = "Requires further investigation using diagnostic queries"
        
        if "container" in description_lower and any(word in description_lower for word in ["stuck", "error", "failure"]):
            root_cause = "Container processing workflow interrupted. Likely causes: EDI message corruption, database lock, or system timeout during container status update."
        elif "vessel" in description_lower and "arrival" in description_lower:
            root_cause = "Vessel arrival processing issue. Possible causes: Port schedule conflict, berth availability problem, or EDI message validation failure."
        elif "edi" in description_lower and "message" in description_lower:
            root_cause = "EDI message processing failure. Common causes: Invalid message format, missing required fields, or communication timeout with external systems."
        elif "gate" in description_lower:
            root_cause = "Terminal gate operation disruption. Potential causes: Access control system malfunction, container verification failure, or database connectivity issue."
        elif "billing" in description_lower:
            root_cause = "Financial transaction processing error. Likely causes: Rate calculation error, missing charge configuration, or invoice generation failure."
        elif any(word in description_lower for word in ["timeout", "slow", "performance"]):
            root_cause = "System performance degradation. Possible causes: Database query optimization needed, high server load, or network latency issues."
        elif any(word in description_lower for word in ["error", "exception", "failure"]):
            root_cause = "Application error detected. Investigate system logs for specific error messages, check database connectivity, and verify service dependencies."
        
        return IncidentAnalysis(
            incident_type=incident_type,
            pattern_match=f"Rule-based match: {incident_type}",
            root_cause=root_cause,
            impact="Operational impact being assessed through system analysis",
            urgency=urgency,
            affected_systems=affected_systems
        )
    
    def _create_fallback_analysis_from_text(self, ai_response: str) -> IncidentAnalysis:
        """Create analysis from AI text response when JSON parsing fails"""
        # Extract information from text response
        lines = ai_response.split('\n')
        
        incident_type = "System Issue"
        root_cause = "Under investigation"
        urgency = "Medium"
        affected_systems = []
        
        for line in lines:
            line_lower = line.lower()
            if "type:" in line_lower or "category:" in line_lower:
                incident_type = line.split(":", 1)[1].strip() if ":" in line else incident_type
            elif "cause:" in line_lower:
                root_cause = line.split(":", 1)[1].strip() if ":" in line else root_cause
            elif "urgency:" in line_lower or "priority:" in line_lower:
                urgency = line.split(":", 1)[1].strip() if ":" in line else urgency
            elif "systems:" in line_lower:
                systems_text = line.split(":", 1)[1].strip() if ":" in line else ""
                if systems_text:
                    affected_systems = [s.strip() for s in systems_text.split(",")]
        
        return IncidentAnalysis(
            incident_type=incident_type[:100] if incident_type else "System Issue",
            pattern_match="AI analysis (text format)",
            root_cause=root_cause[:500] if root_cause else "Under investigation",
            impact="Operational impact being assessed",
            urgency=urgency if urgency in ["Low", "Medium", "High", "Critical"] else "Medium",
            affected_systems=affected_systems[:10]  # Limit to 10 systems
        )
    
    async def generate_resolution_plan_async(self, description: str, analysis: IncidentAnalysis) -> dict:
        """Generate resolution plan using AI based on incident description and analysis"""
        
        if not self.configured:
            logger.warning("Using fallback resolution plan - Azure OpenAI not configured")
            return self._create_fallback_resolution_plan(analysis.incident_type)
        
        try:
            prompt = self._create_resolution_prompt(description, analysis)
            
            request_body = {
                "messages": [
                    {"role": "system", "content": "You are an expert maritime operations specialist providing step-by-step resolution guidance for PORTNET® incidents."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.2
            }
            
            headers = {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            azure_url = f"{self.endpoint}/openai/deployments/{self.deployment_id}/chat/completions?api-version={self.api_version}"
            logger.info(f"Generating resolution plan via Azure OpenAI")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(azure_url, json=request_body, headers=headers, timeout=30.0)
                
                if response.is_success:
                    response_data = response.json()
                    ai_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    logger.info(f"Resolution plan generated successfully")
                    return self._parse_resolution_response(ai_content, analysis.incident_type)
                else:
                    logger.error(f"OpenAI API error for resolution plan: {response.status_code}")
                    return self._create_fallback_resolution_plan(analysis.incident_type)
                    
        except Exception as ex:
            logger.error(f"Error generating resolution plan: {ex}")
            return self._create_fallback_resolution_plan(analysis.incident_type)
    
    def _create_resolution_prompt(self, description: str, analysis: IncidentAnalysis) -> str:
        """Create resolution plan prompt"""
        return f"""Based on this maritime operations incident analysis, create a detailed step-by-step resolution plan:

INCIDENT: {description}

ANALYSIS RESULTS:
- Type: {analysis.incident_type}
- Root Cause: {analysis.root_cause}
- Impact: {analysis.impact}
- Urgency: {analysis.urgency}
- Affected Systems: {', '.join(analysis.affected_systems)}

Please provide a structured resolution plan in JSON format:
{{
    "summary": "Brief summary of the resolution approach",
    "steps": [
        {{
            "order": 1,
            "description": "Specific action to take",
            "type": "Analysis|Investigation|Resolution|Verification",
            "query": "Specific diagnostic query or command if applicable"
        }}
    ]
}}

Focus on:
1. Immediate actions to stabilize the situation
2. Investigation steps to confirm root cause
3. Resolution steps to fix the issue
4. Verification steps to ensure resolution
5. Include specific diagnostic queries for PORTNET®, container systems, EDI processing, etc.
"""
    
    def _parse_resolution_response(self, ai_response: str, incident_type: str) -> dict:
        """Parse AI response into resolution plan"""
        try:
            import json
            # Extract JSON from response
            start = ai_response.find('{')
            end = ai_response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = ai_response[start:end]
                data = json.loads(json_str)
                
                return {
                    "summary": data.get("summary", f"AI-generated resolution plan for {incident_type}"),
                    "steps": data.get("steps", [])
                }
        except Exception as ex:
            logger.error(f"Error parsing resolution response: {ex}")
        
        return self._create_fallback_resolution_plan(incident_type)
    
    def _create_fallback_resolution_plan(self, incident_type: str) -> dict:
        """Create fallback resolution plan when AI is not available"""
        return {
            "summary": f"Structured resolution approach for {incident_type} incident",
            "steps": [
                {
                    "order": 1,
                    "description": "Gather additional incident details and verify system status",
                    "type": "Analysis",
                    "query": "SELECT status FROM system_health WHERE component = 'portnet'"
                },
                {
                    "order": 2,
                    "description": "Identify specific failure points and affected processes", 
                    "type": "Investigation",
                    "query": "SELECT * FROM error_logs WHERE timestamp >= NOW() - INTERVAL 1 HOUR"
                },
                {
                    "order": 3,
                    "description": "Implement targeted fix based on investigation findings",
                    "type": "Resolution",
                    "query": "Apply appropriate system restart or configuration update"
                },
                {
                    "order": 4,
                    "description": "Verify resolution and monitor system stability",
                    "type": "Verification", 
                    "query": "SELECT COUNT(*) FROM error_logs WHERE timestamp >= NOW() - INTERVAL 5 MINUTE"
                }
            ]
        }