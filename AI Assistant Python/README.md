# AI Duty Officer Assistant - Python FastAPI Version

# AI Duty Officer Assistant - Enhanced Edition

A comprehensive maritime operations incident management system powered by Azure OpenAI, featuring automated log analysis, email monitoring, and integrated ticketing workflows.

## 🌟 New Features Added

### 1. 📁 Direct Log Analysis
- **File Upload Interface**: Upload system logs, error logs, and diagnostic files directly through the web interface
- **Multi-Format Support**: Supports .log, .txt, .csv, .json, .xml files
- **AI-Powered Analysis**: Automatically analyzes log content for error patterns, timestamps, and root causes
- **Visual Preview**: Preview log files before submission with syntax highlighting

### 2. 📧 Automated Incident Ingestion
- **Email Monitoring**: Continuously monitors designated email inbox for incident reports
- **Smart Reply Filtering**: Automatically filters out simple replies ("yes", "no", "hello", "thanks") to prevent false incidents
- **AI Classification**: Uses GPT-4 to distinguish genuine incidents from conversational messages
- **Auto-Processing**: Creates incident records automatically from validated email content
- **Confirmation System**: Sends automatic confirmation emails with incident IDs
- **Multi-Source Support**: Handles reports from emails, SMS, phone calls, and system alerts
- **Pattern Recognition**: Detects auto-replies, out-of-office messages, and quoted text

### 3. 🎫 Ticketing and Escalation System
- **Jira Integration**: Automatically creates Jira tickets with AI-generated summaries
- **ServiceNow Support**: Full integration with ServiceNow incident management
- **Executive Summaries**: Generates non-technical summaries for management escalation
- **Smart Priority Detection**: AI determines appropriate priority levels based on content
- **Stakeholder Notifications**: Automatic notifications for high-priority incidents
- **Escalation Workflows**: Configurable escalation paths and timing

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Azure OpenAI account with GPT-4 Vision access
- Email account (Gmail/Outlook) for monitoring
- Optional: Jira or ServiceNow instance for ticketing

### Installation

1. **Clone and Setup**
```bash
cd "AI Assistant Python"
pip install -r requirements.txt
```

2. **Configuration**
```bash
# Copy the example configuration
cp .env.example .env

# Edit .env with your credentials
notepad .env  # On Windows
```

3. **Essential Configuration**
```bash
# Azure OpenAI (Required)
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.azure-api.net

# Email Monitoring (Optional)
EMAIL_MONITORING_ENABLED=true
EMAIL_ADDRESS=incidents@yourcompany.com
EMAIL_PASSWORD=your_app_password

# Ticketing (Optional)
AUTO_CREATE_TICKETS=true
JIRA_URL=https://yourcompany.atlassian.net
JIRA_TOKEN=your_api_token
```

4. **Run the Application**
```bash
python simple_main.py
```

Access at: http://localhost:8002

## Features

- **AI-Powered Analysis**: Uses Azure OpenAI for incident analysis
- **Knowledge Base Integration**: Leverages stored procedures and documentation
- **Training Data System**: Machine learning from historical incidents
- **Dynamic Resolution Plans**: AI-generated resolution steps
- **Web Interface**: Modern responsive design with Bootstrap
- **REST API**: Full API support for integration

## Architecture

### Framework Stack
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation and serialization
- **Jinja2**: Template engine
- **MySQL**: Database backend
- **Bootstrap 5**: Frontend framework

### Project Structure
```
app/
├── models/
│   ├── database.py          # SQLAlchemy models
│   └── schemas.py           # Pydantic schemas
├── services/
│   ├── openai_service.py           # Azure OpenAI integration
│   ├── incident_analyzer.py        # AI incident analysis
│   ├── training_data_service.py    # Training data management
│   └── knowledge_base_service.py   # Knowledge base operations
├── templates/
│   ├── base.html            # Base template
│   ├── index.html           # Home page
│   ├── analyze.html         # Incident analysis form
│   └── results.html         # Analysis results
├── static/                  # Static assets
├── main.py                  # FastAPI application
└── database.py             # Database configuration
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env` file and update with your settings:
- Database connection string
- Azure OpenAI credentials

### 3. Setup Database
The application will create tables automatically on first run.

### 4. Run Application
```bash
# Development mode
python -m app.main

# Production mode with Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Access Application
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative API Docs: http://localhost:8000/redoc

## API Endpoints

### Web Routes
- `GET /` - Home page
- `GET /analyze` - Incident analysis form
- `POST /analyze` - Submit incident for analysis
- `GET /test-case` - Load test case

### API Routes
- `GET /api/training-data` - Get training data
- `POST /api/training-data` - Create training data
- `GET /api/knowledge` - Get knowledge entries
- `POST /api/knowledge` - Create knowledge entry
- `POST /api/knowledge/import-word` - Import from Word document

## Migration from C#

This Python version provides equivalent functionality to the C# ASP.NET version:

| C# Component | Python Equivalent |
|--------------|-------------------|
| ASP.NET Core MVC | FastAPI |
| Entity Framework | SQLAlchemy |
| Dependency Injection | FastAPI dependency system |
| Razor Views | Jinja2 templates |
| HttpClient | httpx |
| ILogger | Python logging |
| C# Models | Pydantic schemas + SQLAlchemy models |

## Configuration

### Environment Variables
All configuration is handled through environment variables in `.env`:
- `DATABASE_URL`: Database connection string
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `AZURE_OPENAI_DEPLOYMENT_ID`: Model deployment ID
- `AZURE_OPENAI_API_VERSION`: API version

### Azure OpenAI Setup
1. Create Azure OpenAI resource
2. Deploy GPT model (recommended: gpt-4)
3. Get API key and endpoint
4. Update configuration in `.env`

## Development

### Adding New Features
1. **Models**: Add to `models/database.py` (SQLAlchemy) and `models/schemas.py` (Pydantic)
2. **Services**: Create service classes in `services/`
3. **Routes**: Add endpoints to `main.py` or create separate router files
4. **Templates**: Add Jinja2 templates to `templates/`

### Database Migrations
While SQLAlchemy can auto-create tables, for production use Alembic:
```bash
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Testing

Run tests with pytest:
```bash
pip install pytest pytest-asyncio
pytest
```

## Deployment

### Production Deployment
1. Use a proper WSGI server like Gunicorn with Uvicorn workers:
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

2. Set up reverse proxy (nginx recommended)
3. Use environment-specific configurations
4. Enable HTTPS
5. Set up monitoring and logging

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## License

This project maintains the same license as the original C# version.