from sqlalchemy.orm import Session
from typing import List
import logging
from .openai_service import OpenAIService
from .training_data_service import TrainingDataService
from .knowledge_base_service import KnowledgeBaseService
from ..models.schemas import IncidentAnalysis

logger = logging.getLogger(__name__)

class IncidentAnalyzer:
    def __init__(self, db: Session):
        self.db = db
        self.openai_service = OpenAIService()
        self.training_service = TrainingDataService(db)
        self.knowledge_service = KnowledgeBaseService(db)
    
    # This function is now correctly indented to be part of the class
    async def analyze_incident_async(self, description: str) -> IncidentAnalysis:
        """
        Analyze incident using AI with training data and knowledge base context
        """
        try:
            logger.info(f"Analyzing incident: {description[:100]}...")
            
            # Get relevant training examples and knowledge
            training_examples = await self.training_service.find_relevant_examples_async(description, 3)
            knowledge_entries = await self.knowledge_service.find_relevant_knowledge_async(description, 5)
            
            logger.info(f"Found {len(training_examples)} training examples and {len(knowledge_entries)} knowledge entries")
            
            # Use OpenAI service for analysis
            analysis = await self.openai_service.analyze_incident_async(description, training_examples, knowledge_entries)
            
            # Generate escalation summary
            analysis.escalation_summary = await self.openai_service.generate_escalation_summary_async(analysis)
            
            logger.info(f"Analysis and escalation summary completed. Type: {analysis.incident_type}, Urgency: {analysis.urgency}")
            
            return analysis
            
        except Exception as ex:
            logger.error(f"Error analyzing incident: {ex}", exc_info=True)
            # Return fallback analysis
            return IncidentAnalysis(
                incident_type="System Issue",
                pattern_match="Error during analysis",
                root_cause="Analysis failed - requires manual investigation",
                impact="Unknown - manual assessment required",
                urgency="Medium",
                affected_systems=["Unknown"],
                escalation_summary="AI analysis failed. Please review the incident manually for escalation."
            )