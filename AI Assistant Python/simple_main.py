from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import logging
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="AI Duty Officer Assistant", version="1.0.0")

# Setup templates with correct path
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(script_dir, "app", "templates")
templates = Jinja2Templates(directory=templates_dir)

# Mock data classes for now
class MockIncident:
    def __init__(self, description, source="Manual"):
        self.id = str(uuid.uuid4())
        self.description = description
        self.source = source
        self.reported_at = datetime.now()
        self.status = "New"

# Import the real services
from app.services.openai_service import OpenAIService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.incident_analyzer import IncidentAnalyzer
from app.models.database import Base
from app.database import get_db, engine
from sqlalchemy.orm import Session

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize the OpenAI service
openai_service = OpenAIService()

class MockResolutionStep:
    def __init__(self, order, description, step_type="Analysis"):
        self.order = order
        self.description = description
        self.type = step_type
        self.query = ""

class MockResolutionPlan:
    def __init__(self, incident_type):
        self.summary = f"Analysis completed for {incident_type}"
        self.steps = [
            MockResolutionStep(1, "Initial assessment completed using AI analysis", "Analysis"),
            MockResolutionStep(2, "Investigate root cause based on analysis findings", "Investigation"),
            MockResolutionStep(3, "Implement resolution based on findings", "Resolution")
        ]
        self.diagnostic_queries = []
        self.resolution_queries = []

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analyze", response_class=HTMLResponse)
async def analyze_get(request: Request):
    """Analyze page - GET"""
    test_cases = [
        {
            "description": "Customer on PORTNET is seeing 2 identical containers information for CMAU0000020",
            "source": "Email",
            "priority": "Medium", 
            "title": "Container Duplication Issue",
            "icon": "fas fa-box",
            "category": "Container Management"
        },
        {
            "description": "VESSEL_ERR_4 when creating vessel advice for MV Lion City 07",
            "source": "Email",
            "priority": "High",
            "title": "Vessel Operations Error", 
            "icon": "fas fa-ship",
            "category": "Vessel Operations"
        },
        {
            "description": "EDI message REF-IFT-0007 stuck in ERROR status, ack_at is NULL",
            "source": "SMS",
            "priority": "High",
            "title": "EDI Processing Failure",
            "icon": "fas fa-exchange-alt",
            "category": "Data Integration"
        }
    ]
    
    return templates.TemplateResponse("analyze.html", {
        "request": request, 
        "test_cases": test_cases
    })

@app.post("/analyze")
async def analyze_post(
    request: Request,
    incident_description: str = Form(...),
    incident_source: str = Form("Manual"),
    db: Session = Depends(get_db)
):
    """Analyze incident - POST"""
    try:
        # Create mock incident
        incident = MockIncident(incident_description, incident_source)
        
        # Use the full IncidentAnalyzer that includes knowledge base integration
        incident_analyzer = IncidentAnalyzer(db)
        analysis = await incident_analyzer.analyze_incident_async(incident_description)
        
        # Generate AI-powered resolution plan
        resolution_data = await openai_service.generate_resolution_plan_async(incident_description, analysis)
        
        # Convert to expected format
        class AIResolutionStep:
            def __init__(self, step_data):
                self.order = step_data.get("order", 1)
                self.description = step_data.get("description", "")
                self.type = step_data.get("type", "Analysis")
                self.query = step_data.get("query", "")
        
        class AIResolutionPlan:
            def __init__(self, resolution_data):
                self.summary = resolution_data.get("summary", "")
                self.steps = [AIResolutionStep(step) for step in resolution_data.get("steps", [])]
                self.diagnostic_queries = []
                self.resolution_queries = []
        
        resolution_plan = AIResolutionPlan(resolution_data)
        
        # Create mock view model
        class MockViewModel:
            def __init__(self, incident, analysis, resolution_plan):
                self.incident = incident
                self.analysis = analysis  
                self.resolution_plan = resolution_plan
        
        view_model = MockViewModel(incident, analysis, resolution_plan)
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "result": view_model
        })
        
    except Exception as ex:
        logger.error(f"Error analyzing incident: {ex}")
        return RedirectResponse(url="/analyze?error=Analysis failed", status_code=302)

@app.get("/test-case")
async def test_case(request: Request, description: str = ""):
    """Test case with preloaded description"""
    return templates.TemplateResponse("analyze.html", {
        "request": request,
        "test_cases": [],
        "preloaded_description": description
    })

@app.get("/upload-knowledge")
async def upload_knowledge_get(request: Request):
    """Knowledge upload page"""
    return templates.TemplateResponse("upload_knowledge.html", {"request": request})

@app.get("/knowledge")
async def view_knowledge(request: Request, db: Session = Depends(get_db)):
    """View knowledge base entries"""
    try:
        knowledge_service = KnowledgeBaseService(db)
        entries = knowledge_service.get_all_knowledge(skip=0, limit=100)
        
        return templates.TemplateResponse("knowledge_list.html", {
            "request": request,
            "entries": entries
        })
    except Exception as ex:
        logger.error(f"Error retrieving knowledge: {ex}")
        return templates.TemplateResponse("knowledge_list.html", {
            "request": request,
            "entries": [],
            "error": f"Error loading knowledge base: {str(ex)}"
        })

@app.post("/upload-knowledge")
async def upload_knowledge_post(
    request: Request, 
    title: str = Form(...), 
    category: str = Form(""), 
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle knowledge upload"""
    try:
        # Use the real knowledge base service
        knowledge_service = KnowledgeBaseService(db)
        result = knowledge_service.import_from_word_content(
            content=content,
            title=title,
            category=category if category else "General",
            source="Web Upload"
        )
        
        logger.info(f"Knowledge uploaded successfully: {title} (ID: {result.id})")
        
        # Return success response
        return templates.TemplateResponse("upload_knowledge.html", {
            "request": request,
            "success": True,
            "message": f"Knowledge document '{title}' uploaded successfully! (ID: {result.id})"
        })
        
    except Exception as ex:
        logger.error(f"Error uploading knowledge: {ex}")
        return templates.TemplateResponse("upload_knowledge.html", {
            "request": request,
            "error": True,
            "message": f"Error uploading document: {str(ex)}"
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)