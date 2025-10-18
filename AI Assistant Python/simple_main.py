from fastapi import FastAPI, Request, Form, Depends, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import logging
from datetime import datetime
import uuid
from dotenv import load_dotenv
import pandas as pd
import io
from typing import List
import base64

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="AI Duty Officer Assistant", version="1.0.0")

# Setup static files
app.mount("/static", StaticFiles(directory="static"), name="static")

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
from app.services.training_data_service import TrainingDataService
from app.services.incident_analyzer import IncidentAnalyzer
from app.models.database import Base
from app.database import get_db, engine
from sqlalchemy.orm import Session

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize the OpenAI service
openai_service = OpenAIService()

async def analyze_image_with_ai(image_content: bytes, content_type: str) -> str:
    """Analyze image using Azure OpenAI Vision API"""
    try:
        # Convert image to base64
        import base64
        encoded_image = base64.b64encode(image_content).decode('utf-8')
        
        # Use Azure OpenAI Vision to analyze the image
        vision_analysis = await openai_service.analyze_image_async(encoded_image, "Maritime incident documentation")
        
        return f"Visual Analysis: {vision_analysis} "
        
    except Exception as ex:
        logger.error(f"Error analyzing image: {ex}")
        return "[Image analysis failed] "

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
    incident_images: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db)
):
    """Analyze incident - POST"""
    try:
        # Process uploaded images
        image_analysis = ""
        uploaded_images = []
        
        if incident_images and incident_images[0].filename:  # Check if actual files were uploaded
            logger.info(f"Processing {len(incident_images)} uploaded images")
            
            # Create uploads directory if it doesn't exist
            import os
            uploads_dir = os.path.join(os.path.dirname(__file__), "static", "uploads")
            os.makedirs(uploads_dir, exist_ok=True)
            
            for image in incident_images:
                if image.filename and image.content_type.startswith('image/'):
                    # Save image
                    import uuid
                    file_extension = os.path.splitext(image.filename)[1]
                    unique_filename = f"{uuid.uuid4()}{file_extension}"
                    file_path = os.path.join(uploads_dir, unique_filename)
                    
                    content = await image.read()
                    with open(file_path, "wb") as f:
                        f.write(content)
                    
                    uploaded_images.append({
                        "filename": unique_filename,
                        "original_name": image.filename,
                        "path": f"/static/uploads/{unique_filename}",
                        "size": len(content)
                    })
                    
                    # Analyze image with AI vision (placeholder for now)
                    image_analysis += await analyze_image_with_ai(content, image.content_type)
        
        # Combine text description with image analysis
        combined_description = incident_description
        if image_analysis:
            combined_description += f"\n\nImage Analysis:\n{image_analysis}"
        
        # Create mock incident
        incident = MockIncident(combined_description, incident_source)
        
        # Use the full IncidentAnalyzer that includes knowledge base integration
        incident_analyzer = IncidentAnalyzer(db)
        analysis = await incident_analyzer.analyze_incident_async(combined_description)
        
        # Generate AI-powered resolution plan
        resolution_data = await openai_service.generate_resolution_plan_async(combined_description, analysis)
        
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
            def __init__(self, incident, analysis, resolution_plan, uploaded_images=None):
                self.incident = incident
                self.analysis = analysis  
                self.resolution_plan = resolution_plan
                self.uploaded_images = uploaded_images or []
        
        view_model = MockViewModel(incident, analysis, resolution_plan, uploaded_images)
        
        return templates.TemplateResponse("results.html", {
            "request": request,
            "result": view_model,
            "uploaded_images": uploaded_images
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

@app.get("/training")
async def view_training(request: Request, db: Session = Depends(get_db)):
    """View training data entries"""
    try:
        from app.models.database import TrainingData
        training_data = db.query(TrainingData).order_by(TrainingData.created_at.desc()).all()
        
        return templates.TemplateResponse("training.html", {
            "request": request,
            "training_data": training_data
        })
    except Exception as ex:
        logger.error(f"Error retrieving training data: {ex}")
        return templates.TemplateResponse("training.html", {
            "request": request,
            "training_data": [],
            "error": f"Error loading training data: {str(ex)}"
        })

@app.get("/database-status")
async def database_status(request: Request, db: Session = Depends(get_db)):
    """View database status and contents"""
    try:
        from app.models.database import KnowledgeBase, TrainingData
        
        # Count entries
        kb_count = db.query(KnowledgeBase).count()
        td_count = db.query(TrainingData).count()
        
        # Get recent knowledge entries
        recent_knowledge = db.query(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()).limit(10).all()
        
        # Get recent training data
        recent_training = db.query(TrainingData).order_by(TrainingData.created_at.desc()).limit(5).all()
        
        return templates.TemplateResponse("database_status.html", {
            "request": request,
            "kb_count": kb_count,
            "td_count": td_count,
            "recent_knowledge": recent_knowledge,
            "recent_training": recent_training
        })
    except Exception as ex:
        logger.error(f"Error retrieving database status: {ex}")
        return {"error": str(ex)}

@app.get("/sql-export")
async def sql_export(request: Request):
    """Export database as SQL"""
    try:
        import sqlite3
        
        # Connect to database
        conn = sqlite3.connect('duty_officer_assistant.db')
        cursor = conn.cursor()
        
        sql_content = []
        sql_content.append("-- =====================================================")
        sql_content.append("-- DUTY OFFICER ASSISTANT DATABASE EXPORT")
        sql_content.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sql_content.append("-- =====================================================\n")
        
        # Get table schemas and data
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table_name in tables:
            table = table_name[0]
            sql_content.append(f"\n-- ===== TABLE: {table.upper()} =====")
            
            # Get table schema
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'")
            schema = cursor.fetchone()
            if schema:
                sql_content.append(f"-- Schema:")
                sql_content.append(schema[0] + ";")
                sql_content.append("")
            
            # Get table data count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            sql_content.append(f"-- Records: {count}")
            
            if count > 0:
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Get all data
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                
                sql_content.append(f"\n-- Data for {table}:")
                for i, row in enumerate(rows):
                    insert_values = []
                    for value in row:
                        if value is None:
                            insert_values.append("NULL")
                        elif isinstance(value, str):
                            escaped_value = value.replace("'", "''")
                            insert_values.append(f"'{escaped_value}'")
                        else:
                            insert_values.append(str(value))
                    
                    column_list = "(" + ", ".join(columns) + ")"
                    values_list = "(" + ", ".join(insert_values) + ")"
                    sql_content.append(f"INSERT INTO {table} {column_list}")
                    sql_content.append(f"VALUES {values_list};")
                    sql_content.append("")
            
            sql_content.append(f"-- End of {table.upper()}")
            sql_content.append("-" * 60)
        
        conn.close()
        
        # Return as plain text response
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse("\n".join(sql_content), media_type="text/plain")
        
    except Exception as ex:
        logger.error(f"Error exporting SQL: {ex}")
        return PlainTextResponse(f"Error exporting database: {str(ex)}", media_type="text/plain")

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

@app.get("/upload-training", response_class=HTMLResponse)
async def upload_training(request: Request):
    """Upload training data page"""
    return templates.TemplateResponse("upload_training.html", {"request": request})

@app.post("/upload-training-data")
async def upload_training_data(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Handle training data upload"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            return templates.TemplateResponse("upload_training.html", {
                "request": request,
                "error": True,
                "message": "Please upload an Excel file (.xlsx or .xls)"
            })
        
        # Read Excel file
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        if df.empty:
            return templates.TemplateResponse("upload_training.html", {
                "request": request,
                "error": True,
                "message": "Excel file is empty"
            })
        
        # Intelligent column detection
        training_service = TrainingDataService(db)
        
        # Detect columns based on content patterns
        incident_col = None
        resolution_col = None
        
        # Look for incident-related columns
        for col in df.columns:
            col_lower = str(col).lower()
            sample_data = df[col].dropna().astype(str).str.lower()
            
            # Check if this looks like an incident column
            if any(keyword in col_lower for keyword in ['incident', 'problem', 'issue', 'description', 'summary', 'title']):
                incident_col = col
            # Check if this looks like a resolution column  
            elif any(keyword in col_lower for keyword in ['resolution', 'solution', 'fix', 'action', 'steps', 'procedure']):
                resolution_col = col
            # Content-based detection
            elif not incident_col and sample_data.str.contains('error|failed|down|issue|problem', na=False).any():
                incident_col = col
            elif not resolution_col and sample_data.str.contains('restart|check|verify|contact|replace', na=False).any():
                resolution_col = col
        
        # If no specific columns found, try first two text columns
        if not incident_col or not resolution_col:
            text_cols = [col for col in df.columns if df[col].dtype == 'object']
            if len(text_cols) >= 2:
                if not incident_col:
                    incident_col = text_cols[0]
                if not resolution_col:
                    resolution_col = text_cols[1]
            elif len(text_cols) == 1:
                incident_col = text_cols[0]
                resolution_col = text_cols[0]  # Use same column for both
        
        if not incident_col:
            return templates.TemplateResponse("upload_training.html", {
                "request": request,
                "error": True,
                "message": f"Could not identify incident column. Available columns: {list(df.columns)}"
            })
        
        # Process the data
        success_count = 0
        error_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                incident_text = str(row[incident_col]).strip()
                resolution_text = str(row[resolution_col]).strip() if resolution_col else ""
                
                if incident_text and incident_text.lower() not in ['nan', 'none', '']:
                    result = training_service.add_training_example(
                        incident_description=incident_text,
                        resolution_steps=resolution_text,
                        source=f"Excel Upload: {file.filename}",
                        category="Imported"
                    )
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"Row {index + 1}: Empty incident description")
                    
            except Exception as ex:
                error_count += 1
                errors.append(f"Row {index + 1}: {str(ex)}")
        
        # Prepare result message
        message = f"Successfully imported {success_count} training examples"
        if incident_col:
            message += f" (Incident column: '{incident_col}'"
        if resolution_col and resolution_col != incident_col:
            message += f", Resolution column: '{resolution_col}'"
        if incident_col:
            message += ")"
        
        if error_count > 0:
            message += f". {error_count} errors occurred."
        
        return templates.TemplateResponse("upload_training.html", {
            "request": request,
            "success": True,
            "message": message,
            "details": {
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors[:10],  # Show first 10 errors
                "incident_column": incident_col,
                "resolution_column": resolution_col,
                "total_rows": len(df)
            }
        })
        
    except Exception as ex:
        logger.error(f"Error uploading training data: {ex}")
        return templates.TemplateResponse("upload_training.html", {
            "request": request,
            "error": True,
            "message": f"Error processing file: {str(ex)}"
        })

@app.get("/view-training")
async def view_training_old(request: Request, db: Session = Depends(get_db)):
    """View training data"""
    try:
        from app.models.database import TrainingData
        training_data = db.query(TrainingData).order_by(TrainingData.created_at.desc()).limit(50).all()
        
        return templates.TemplateResponse("database_status.html", {
            "request": request,
            "training_data": training_data,
            "view_type": "training"
        })
    except Exception as ex:
        logger.error(f"Error retrieving training data: {ex}")
        return {"error": str(ex)}

@app.delete("/api/training/{training_id}")
async def delete_training(training_id: int, db: Session = Depends(get_db)):
    """Delete a training data entry"""
    try:
        from app.models.database import TrainingData
        
        # Find the training entry
        training_entry = db.query(TrainingData).filter(TrainingData.id == training_id).first()
        
        if not training_entry:
            return {"error": "Training data not found"}
        
        # Delete the entry
        db.delete(training_entry)
        db.commit()
        
        logger.info(f"Training data deleted: ID {training_id}")
        return {"message": "Training data deleted successfully"}
        
    except Exception as ex:
        logger.error(f"Error deleting training data: {ex}")
        db.rollback()
        return {"error": str(ex)}

@app.delete("/api/knowledge/{knowledge_id}")
async def delete_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    """Delete a knowledge base entry"""
    try:
        from app.models.database import KnowledgeBase
        
        # Find the knowledge entry
        knowledge_entry = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_id).first()
        
        if not knowledge_entry:
            return {"error": "Knowledge entry not found"}
        
        # Delete the entry
        db.delete(knowledge_entry)
        db.commit()
        
        logger.info(f"Knowledge entry deleted: ID {knowledge_id}")
        return {"message": "Knowledge entry deleted successfully"}
        
    except Exception as ex:
        logger.error(f"Error deleting knowledge entry: {ex}")
        db.rollback()
        return {"error": str(ex)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)