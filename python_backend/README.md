# Resume Fraud Detection API

A Python 3.11+ FastAPI service for comprehensive resume fraud detection using AI and metadata analysis.

## Features

- **AI Content Detection**: Uses Amazon Bedrock (Claude Sonnet 4) to detect AI-generated text
- **Document Authenticity**: Analyzes PDF/DOCX metadata for fraud indicators
- **Contact Verification**: Validates email addresses and phone numbers using external APIs
- **Professional Background**: LinkedIn and company verification (placeholder)
- **Digital Footprint**: Social media and search engine analysis (placeholder)
- **Comprehensive Reporting**: Aggregated risk assessment with detailed rationale

## Architecture

```
python_backend/
├── detectors/           # Individual fraud detection modules
│   ├── ai_text.py      # AI content detection
│   ├── document_auth.py # Document authenticity analysis
│   └── contact_info.py  # Contact information verification
├── orchestrator/        # Main analysis orchestrator
│   └── analyzer.py     # Coordinates all detectors
├── models/             # Pydantic schemas
│   └── schemas.py      # API request/response models
├── storage/            # Data persistence
│   └── supabase_client.py # Supabase integration
├── utils/              # Utilities and configuration
│   ├── config.py       # Settings management
│   └── logging_config.py # Structured logging
└── main.py            # FastAPI application
```

## Setup

### Prerequisites

- Python 3.11+
- pip or poetry
- AWS account with Bedrock access
- Supabase account
- Redis (optional, for caching)

### Installation

1. **Clone and navigate to the Python backend:**
   ```bash
   cd python_backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your actual credentials
   ```

5. **Run the service:**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /analyze
Comprehensive resume analysis endpoint.

**Request:**
- `file`: PDF or DOCX file (multipart/form-data)
- `candidate_hints`: Optional JSON with candidate information

**Response:**
```json
{
  "extractedText": "Resume text content...",
  "candidateInfo": {
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "location": "New York, NY"
  },
  "aiDetection": {
    "is_ai_generated": false,
    "confidence": 25,
    "model": "claude-sonnet-4"
  },
  "documentAuthenticity": {
    "authenticityScore": 85,
    "suspiciousIndicators": [],
    "rationale": "Document appears authentic"
  },
  "aggregatedReport": {
    "overall_score": 45,
    "slices": [...],
    "evidence": {...}
  }
}
```

### POST /ai-detect
Standalone AI content detection.

**Request:**
- `text`: Text content to analyze
- `model`: AI model to use (optional)

### POST /document-authenticity
Document metadata analysis.

**Request:**
- `file`: PDF or DOCX file

### POST /contact-verify
Contact information verification.

**Request:**
- `email`: Email address
- `phone`: Phone number (optional)
- `location`: Location (optional)

## Configuration

### Required Environment Variables

- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (default: us-east-1)
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon key

### Optional Environment Variables

- `NUMVERIFY_API_KEY`: For phone number verification
- `ABSTRACT_API_KEY`: For email verification
- `SERPAPI_KEY`: For search engine queries
- `REDIS_URL`: Redis connection string
- `DEBUG`: Enable debug mode
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

## Development

### Code Quality

```bash
# Format code
black .
isort .

# Type checking
mypy .

# Run tests
pytest
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_ai_detector.py
```

## Integration with Next.js Frontend

The Python backend is designed to work with the existing Next.js frontend. Update your Next.js API routes to call the Python service:

```typescript
// In your Next.js API route
const response = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  body: formData
});
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

### Production Considerations

- Use a production ASGI server (e.g., Gunicorn with Uvicorn workers)
- Set up Redis for caching and rate limiting
- Configure proper logging and monitoring
- Use environment-specific configuration files
- Set up health checks and metrics endpoints

## License

MIT License
