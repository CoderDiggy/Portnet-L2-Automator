from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Optional
import json

Base = declarative_base()

class TrainingData(Base):
    __tablename__ = "training_data"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_description = Column(Text, nullable=False)
    expected_incident_type = Column(String(255), default="")
    expected_pattern_match = Column(String(255), default="")
    expected_root_cause = Column(Text, default="")
    expected_impact = Column(Text, default="")
    expected_urgency = Column(String(50), default="")
    expected_affected_systems_json = Column(Text, default="")
    category = Column(String(255), default="")
    tags = Column(Text, default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), default="")
    is_validated = Column(Integer, default=0)  # 0=No, 1=Yes
    
    @property
    def expected_affected_systems(self) -> List[str]:
        """Get affected systems as a list"""
        if not self.expected_affected_systems_json:
            return []
        try:
            return json.loads(self.expected_affected_systems_json)
        except:
            return []
    
    @expected_affected_systems.setter
    def expected_affected_systems(self, value: List[str]):
        """Set affected systems from a list"""
        self.expected_affected_systems_json = json.dumps(value)
    
    def calculate_similarity(self, query: str) -> float:
        """Calculate similarity score with a query"""
        query_lower = query.lower()
        description_lower = self.incident_description.lower()
        
        # Simple keyword matching score
        query_words = set(query_lower.split())
        description_words = set(description_lower.split())
        
        if not query_words:
            return 0.0
        
        # Jaccard similarity
        intersection = query_words.intersection(description_words)
        union = query_words.union(description_words)
        
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Bonus for exact phrase matches
        phrase_bonus = 0.2 if query_lower in description_lower else 0.0
        
        # Category match bonus
        category_bonus = 0.1 if self.category.lower() in query_lower else 0.0
        
        return min(jaccard + phrase_bonus + category_bonus, 1.0)


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(255), default="")
    type = Column(String(100), default="")  # Procedure, FAQ, Solution, Reference
    tags = Column(Text, default="")
    keywords = Column(Text, default="")
    priority = Column(Integer, default=1)  # 1=Low, 2=Medium, 3=High, 4=Critical
    source = Column(String(255), default="")  # Word Doc, Manual Entry, Import
    status = Column(String(50), default="Active")  # Active, Inactive, Draft
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), default="")
    version_notes = Column(Text, default="")
    view_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    
    def calculate_relevance(self, query: str) -> float:
        """Calculate relevance score for a given query"""
        query_lower = query.lower()
        content_lower = self.content.lower()
        title_lower = self.title.lower()
        keywords_lower = self.keywords.lower()
        
        score = 0.0
        
        # Title exact match (highest weight)
        if query_lower in title_lower:
            score += 0.4
        
        # Content contains query
        if query_lower in content_lower:
            score += 0.3
        
        # Keywords match
        if query_lower in keywords_lower:
            score += 0.2
        
        # Word-level matching
        query_words = set(query_lower.split())
        title_words = set(title_lower.split())
        content_words = set(content_lower.split())
        
        # Title word matches
        title_matches = len(query_words.intersection(title_words))
        if title_matches > 0:
            score += 0.2 * (title_matches / len(query_words))
        
        # Content word matches
        content_matches = len(query_words.intersection(content_words))
        if content_matches > 0:
            score += 0.1 * (content_matches / len(query_words))
        
        # Priority bonus
        priority_bonus = self.priority * 0.05
        score += priority_bonus
        
        # Usage bonus (recently used items get slight boost)
        if self.last_used and self.view_count > 0:
            days_since_use = (datetime.utcnow() - self.last_used).days
            usage_bonus = min(0.1, self.view_count * 0.01 / max(days_since_use, 1))
            score += usage_bonus
        
        return min(score, 1.0)

# Enhanced Database Models for New Features

class Incident(Base):
    """Enhanced incident model with full tracking capabilities"""
    __tablename__ = "incidents"
    
    id = Column(String(255), primary_key=True)  # UUID string
    description = Column(Text, nullable=False)
    source = Column(String(50), default="Manual")  # Manual, Email, SMS, Call, System
    priority = Column(String(20), default="Medium")  # Critical, High, Medium, Low
    title = Column(String(500), default="")
    category = Column(String(255), default="System Issue")
    status = Column(String(50), default="New")  # New, In Progress, Resolved, Closed
    assigned_to = Column(String(255), default="")
    
    # Timestamps
    reported_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # AI Analysis Results
    ai_analysis = Column(Text, default="")
    resolution_plan_json = Column(Text, default="")
    
    @property
    def resolution_plan(self) -> dict:
        """Get resolution plan as dict"""
        if not self.resolution_plan_json:
            return {}
        try:
            return json.loads(self.resolution_plan_json)
        except:
            return {}
    
    @resolution_plan.setter
    def resolution_plan(self, value: dict):
        """Set resolution plan from dict"""
        self.resolution_plan_json = json.dumps(value)

class LogFile(Base):
    """Log files attached to incidents"""
    __tablename__ = "log_files"
    
    id = Column(String(255), primary_key=True)  # UUID string
    incident_id = Column(String(255), nullable=True)  # Foreign key to incidents
    filename = Column(String(500), nullable=False)
    original_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, default=0)
    content_type = Column(String(100), default="text/plain")
    analysis_result = Column(Text, default="")
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

class EmailIncident(Base):
    """Email-based incidents"""
    __tablename__ = "email_incidents"
    
    id = Column(String(255), primary_key=True)  # UUID string
    incident_id = Column(String(255), nullable=True)  # Foreign key to incidents
    sender = Column(String(500), nullable=False)
    subject = Column(String(1000), nullable=False)
    email_content = Column(Text, nullable=False)
    received_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    classification = Column(String(50), default="Incident")  # Incident, Spam, Information
    auto_created = Column(Integer, default=1)  # 0=No, 1=Yes
    ai_extracted_data_json = Column(Text, default="")
    
    @property
    def ai_extracted_data(self) -> dict:
        """Get extracted data as dict"""
        if not self.ai_extracted_data_json:
            return {}
        try:
            return json.loads(self.ai_extracted_data_json)
        except:
            return {}
    
    @ai_extracted_data.setter
    def ai_extracted_data(self, value: dict):
        """Set extracted data from dict"""
        self.ai_extracted_data_json = json.dumps(value)

class Ticket(Base):
    """Tickets created in external systems"""
    __tablename__ = "tickets"
    
    id = Column(String(255), primary_key=True)  # UUID string
    incident_id = Column(String(255), nullable=False)  # Foreign key to incidents
    ticket_system = Column(String(50), nullable=False)  # Jira, ServiceNow, Internal
    ticket_id = Column(String(255), nullable=False)  # External ticket ID
    ticket_url = Column(String(1000), default="")
    priority = Column(String(20), default="Medium")
    status = Column(String(50), default="Open")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    escalation_data_json = Column(Text, default="")
    
    @property
    def escalation_data(self) -> dict:
        """Get escalation data as dict"""
        if not self.escalation_data_json:
            return {}
        try:
            return json.loads(self.escalation_data_json)
        except:
            return {}
    
    @escalation_data.setter
    def escalation_data(self, value: dict):
        """Set escalation data from dict"""
        self.escalation_data_json = json.dumps(value)

class Escalation(Base):
    """Escalation records for high-priority incidents"""
    __tablename__ = "escalations"
    
    id = Column(String(255), primary_key=True)  # UUID string
    incident_id = Column(String(255), nullable=False)  # Foreign key to incidents
    ticket_id = Column(String(255), nullable=True)  # Foreign key to tickets
    
    executive_summary = Column(Text, nullable=False)
    business_impact = Column(Text, nullable=False)
    urgency_justification = Column(Text, nullable=False)
    resource_requirements = Column(Text, nullable=False)
    estimated_resolution_time = Column(String(100), nullable=False)
    escalation_level = Column(String(20), default="Medium")  # Low, Medium, High, Critical
    
    stakeholder_notification_json = Column(Text, default="[]")
    notifications_sent = Column(Integer, default=0)  # 0=No, 1=Yes
    
    created_at = Column(DateTime, default=datetime.utcnow)
    notified_at = Column(DateTime, nullable=True)
    
    @property
    def stakeholder_notification(self) -> List[str]:
        """Get stakeholder list"""
        if not self.stakeholder_notification_json:
            return []
        try:
            return json.loads(self.stakeholder_notification_json)
        except:
            return []
    
    @stakeholder_notification.setter
    def stakeholder_notification(self, value: List[str]):
        """Set stakeholder list"""
        self.stakeholder_notification_json = json.dumps(value)