from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import logging
import os
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="AI Duty Officer Assistant", version="1.0.0")

# Setup templates  
templates = Jinja2Templates(directory="app/templates")

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analyze", response_class=HTMLResponse)
async def analyze_get(request: Request):
    """Analyze page - GET"""
    # Test cases similar to C# version
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
        },
        {
            "description": "BAPLIE inconsistency for MV PACIFIC DAWN/07E: COARRI shows load completed but BAPLIE still lists units",
            "source": "Call",
            "priority": "Critical",
            "title": "Stowage Planning Mismatch",
            "icon": "fas fa-clipboard-list",
            "category": "Cargo Operations"
        },
        {
            "description": "Terminal gate system showing 'ACCESS_DENIED' for valid truck appointments with containers TRLU1234567, GESU9876543",
            "source": "Call",
            "priority": "High",
            "title": "Gate Access Control Issue",
            "icon": "fas fa-truck",
            "category": "Terminal Operations"
        },
        {
            "description": "Billing discrepancy: Invoice INV-2024-10-15-001 shows incorrect demurrage charges for containers that were collected on time",
            "source": "Email",
            "priority": "Medium",
            "title": "Billing System Error",
            "icon": "fas fa-receipt",
            "category": "Financial Operations"
        }
    ]
    
    return templates.TemplateResponse("analyze.html", {
        "request": request, 
        "test_cases": test_cases
    })

@app.post("/analyze")
async def analyze_post(
    incident_description: str = Form(...),
    incident_source: str = Form("Manual"),
    db: Session = Depends(get_db)
):
    """Analyze incident - POST"""
    try:
        # Create incident
        incident = schemas.Incident(
            description=incident_description,
            source=incident_source
        )
        
        # Analyze incident
        analyzer = IncidentAnalyzer(db)
        analysis = await analyzer.analyze_incident_async(incident.description)
        
        # For now, create a simple resolution plan (can be enhanced later)
        resolution_plan = schemas.ResolutionPlan(
            summary=f"Analysis completed for {analysis.incident_type}",
            steps=[
                schemas.ResolutionStep(
                    order=1,
                    description="Initial assessment completed using AI analysis",
                    type="Analysis"
                ),
                schemas.ResolutionStep(
                    order=2,
                    description="Investigate root cause based on analysis findings",
                    type="Investigation"
                )
            ]
        )
        
        # Create view model
        view_model = schemas.AnalysisResultViewModel(
            incident=incident,
            analysis=analysis,
            resolution_plan=resolution_plan
        )
        
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
    test_cases = []  # You can populate this if needed
    return templates.TemplateResponse("analyze.html", {
        "request": request,
        "test_cases": test_cases,
        "preloaded_description": description
    })

# API Routes for Training Data
@app.get("/api/training-data", response_model=List[schemas.TrainingDataResponse])
async def get_training_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get training data"""
    service = TrainingDataService(db)
    return service.get_all_training_data(skip=skip, limit=limit)

@app.post("/api/training-data", response_model=schemas.TrainingDataResponse)
async def create_training_data(training_data: schemas.TrainingDataCreate, db: Session = Depends(get_db)):
    """Create training data"""
    service = TrainingDataService(db)
    return service.create_training_data(training_data)

# API Routes for Knowledge Base
@app.get("/api/knowledge", response_model=List[schemas.KnowledgeBaseResponse])
async def get_knowledge(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get knowledge entries"""
    service = KnowledgeBaseService(db)
    return service.get_all_knowledge(skip=skip, limit=limit)

@app.post("/api/knowledge", response_model=schemas.KnowledgeBaseResponse)
async def create_knowledge(knowledge_data: schemas.KnowledgeBaseCreate, db: Session = Depends(get_db)):
    """Create knowledge entry"""
    service = KnowledgeBaseService(db)
    return service.create_knowledge(knowledge_data)

@app.post("/api/knowledge/import-word")
async def import_word_document(
    content: str = Form(...),
    title: str = Form(...),
    category: str = Form(""),
    db: Session = Depends(get_db)
):
    """Import knowledge from Word document content"""
    service = KnowledgeBaseService(db)
    result = service.import_from_word_content(content, title, category)
    return {"message": "Document imported successfully", "id": result.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)