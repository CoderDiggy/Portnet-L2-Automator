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