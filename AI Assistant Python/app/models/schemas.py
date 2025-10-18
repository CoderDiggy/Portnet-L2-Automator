from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

# Incident Models
class IncidentBase(BaseModel):
    description: str = ""
    source: str = "Manual"  # Email, SMS, Call, Manual
    priority: str = "Medium"
    title: str = ""
    icon: str = "fas fa-exclamation-circle"
    category: str = "System Issue"

class IncidentCreate(IncidentBase):
    pass

class Incident(IncidentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "New"
    assigned_to: str = ""
    
    class Config:
        from_attributes = True

# Analysis Models
class IncidentAnalysis(BaseModel):
    incident_type: str = ""
    pattern_match: str = ""
    root_cause: str = ""
    impact: str = ""
    urgency: str = "Medium"
    affected_systems: List[str] = []
    
    class Config:
        from_attributes = True

# Resolution Models
class ResolutionStep(BaseModel):
    order: int
    description: str = ""
    query: str = ""
    type: str = "Diagnostic"  # Diagnostic, Resolution, Verification

class ResolutionPlan(BaseModel):
    steps: List[ResolutionStep] = []
    diagnostic_queries: List[str] = []
    resolution_queries: List[str] = []
    summary: str = ""

# Enhanced Features Schemas

# Log File Models
class LogFileBase(BaseModel):
    filename: str
    original_name: str
    file_path: str
    file_size: int
    content_type: str = "text/plain"
    analysis_result: Optional[str] = None

class LogFileCreate(LogFileBase):
    pass

class LogFile(LogFileBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    incident_id: Optional[str] = None
    
    class Config:
        from_attributes = True

# Email Incident Models
class EmailIncidentBase(BaseModel):
    sender: str
    subject: str
    email_content: str
    received_at: datetime
    classification: str = "Incident"  # Incident, Spam, Information

class EmailIncidentCreate(EmailIncidentBase):
    pass

class EmailIncident(EmailIncidentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    incident_id: Optional[str] = None
    auto_created: bool = True
    ai_extracted_data: Optional[dict] = None
    
    class Config:
        from_attributes = True

# Ticket Integration Models
class TicketBase(BaseModel):
    ticket_system: str  # Jira, ServiceNow, Internal
    ticket_id: str
    ticket_url: Optional[str] = None
    priority: str = "Medium"
    status: str = "Open"

class TicketCreate(TicketBase):
    pass

class Ticket(TicketBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    incident_id: str
    escalation_data: Optional[dict] = None
    
    class Config:
        from_attributes = True

# Escalation Models
class EscalationSummary(BaseModel):
    executive_summary: str
    business_impact: str
    urgency_justification: str
    resource_requirements: str
    estimated_resolution_time: str
    stakeholder_notification: List[str] = []
    escalation_level: str = "Medium"  # Low, Medium, High, Critical

class EscalationCreate(EscalationSummary):
    pass

class Escalation(EscalationSummary):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    incident_id: str
    ticket_id: Optional[str] = None
    notifications_sent: bool = False
    
    class Config:
        from_attributes = True

# Enhanced Incident Model with new relationships
class EnhancedIncident(IncidentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "New"
    assigned_to: str = ""
    
    # New relationships
    log_files: List[LogFile] = []
    email_source: Optional[EmailIncident] = None
    tickets: List[Ticket] = []
    escalations: List[Escalation] = []
    
    # AI Analysis results
    ai_analysis: Optional[str] = None
    resolution_plan: Optional[dict] = None
    
    class Config:
        from_attributes = True
    
    class Config:
        from_attributes = True

# Training Data Models
class TrainingDataBase(BaseModel):
    incident_description: str
    expected_incident_type: str = ""
    expected_pattern_match: str = ""
    expected_root_cause: str = ""
    expected_impact: str = ""
    expected_urgency: str = ""
    expected_affected_systems: List[str] = []
    category: str = ""
    tags: str = ""
    notes: str = ""
    created_by: str = ""
    is_validated: bool = False

class TrainingDataCreate(TrainingDataBase):
    pass

class TrainingDataUpdate(BaseModel):
    incident_description: Optional[str] = None
    expected_incident_type: Optional[str] = None
    expected_pattern_match: Optional[str] = None
    expected_root_cause: Optional[str] = None
    expected_impact: Optional[str] = None
    expected_urgency: Optional[str] = None
    expected_affected_systems: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None
    is_validated: Optional[bool] = None

class TrainingDataResponse(TrainingDataBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Knowledge Base Models
class KnowledgeBaseBase(BaseModel):
    title: str
    content: str
    category: str = ""
    type: str = ""  # Procedure, FAQ, Solution, Reference
    tags: str = ""
    keywords: str = ""
    priority: int = 1  # 1=Low, 2=Medium, 3=High, 4=Critical
    source: str = ""  # Word Doc, Manual Entry, Import
    status: str = "Active"  # Active, Inactive, Draft
    created_by: str = ""
    version_notes: str = ""

class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass

class KnowledgeBaseUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    tags: Optional[str] = None
    keywords: Optional[str] = None
    priority: Optional[int] = None
    source: Optional[str] = None
    status: Optional[str] = None
    version_notes: Optional[str] = None

class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    view_count: int = 0
    last_used: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Analysis Result View Model
class AnalysisResultViewModel(BaseModel):
    incident: Incident
    analysis: IncidentAnalysis
    resolution_plan: ResolutionPlan
    
    class Config:
        from_attributes = True

# API Response Models
class AnalyzeRequest(BaseModel):
    incident_description: str
    incident_source: str = "Manual"

class WordDocImportRequest(BaseModel):
    content: str
    title: str
    category: str = ""
    source: str = "Word Document Import"