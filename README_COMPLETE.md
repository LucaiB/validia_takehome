# SentinelHire - AI-Powered Resume Fraud Detection System

A comprehensive fraud detection system that analyzes resumes for authenticity, verifies candidate information, and provides multi-dimensional risk assessment using AI and external APIs.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OR Node.js 18+ and Python 3.11+

### Option 1: Docker (Recommended)
```bash
# Clone the repository
git clone https://github.com/LucaiB/validia_takehome.git
cd validia_takehome

# Build and run with Docker Compose
docker-compose up --build

# The API will be available at http://localhost:8000
# The frontend will be available at http://localhost:3000
```

### Option 2: Local Development
```bash
# Clone the repository
git clone https://github.com/LucaiB/validia_takehome.git
cd validia_takehome

# Install frontend dependencies
pnpm install

# Install Python dependencies
cd python_backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start the backend
python3 main.py

# In another terminal, start the frontend
pnpm dev
```

## 🔧 API Usage

### Main Analysis Endpoint
```bash
# Analyze a resume file
curl -F file=@samples/sample_resume_1.txt http://localhost:8000/analyze | jq
```

### Sample Request/Response

**Request:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@samples/sample_resume_1.txt" \
  -F "candidate_hints={\"full_name\":\"John Smith\",\"email\":\"john.smith@email.com\"}"
```

**Response:**
```json
{
  "extractedText": "John Smith\nSoftware Engineer\njohn.smith@email.com...",
  "candidateInfo": {
    "full_name": "John Smith",
    "email": "john.smith@email.com",
    "phone": "(555) 123-4567",
    "location": "San Francisco, CA"
  },
  "aiDetection": {
    "is_ai_generated": false,
    "confidence": 25,
    "model": "claude-sonnet-4-heuristic",
    "rationale": "Heuristic analysis suggests human-written content"
  },
  "documentAuthenticity": {
    "fileName": "sample_resume_1.txt",
    "fileSize": 1024,
    "fileType": "text/plain",
    "authenticityScore": 85,
    "rationale": "Document appears authentic with consistent formatting"
  },
  "contactVerification": {
    "email": "john.smith@email.com",
    "is_verified": true,
    "email_valid": true,
    "email_disposable": false,
    "phone_valid": true,
    "details": "Email and phone validation completed successfully"
  },
  "aggregatedReport": {
    "overall_score": 35,
    "weights_applied": {
      "ai_content": 0.35,
      "contact_info": 0.25,
      "document_authenticity": 0.1
    },
    "slices": [
      {
        "label": "AI Content",
        "score": 25,
        "description": "Heuristic analysis suggests human-written content"
      },
      {
        "label": "Contact Info",
        "score": 20,
        "description": "Email and phone validation completed successfully"
      },
      {
        "label": "Document Authenticity",
        "score": 85,
        "description": "Document appears authentic with consistent formatting"
      }
    ],
    "evidence": {
      "ai": {
        "is_ai_generated": false,
        "confidence": 25,
        "model": "claude-sonnet-4-heuristic"
      },
      "contact": {
        "email_valid": true,
        "email_disposable": false,
        "phone_valid": true
      },
      "document_authenticity": {
        "authenticityScore": 85,
        "suspiciousIndicators": []
      }
    },
    "rationale": [
      "Low risk profile based on comprehensive analysis",
      "Contact information appears legitimate",
      "Document formatting suggests authentic creation"
    ],
    "generated_at": "2025-01-16T18:00:00Z",
    "version": "1.0.0"
  }
}
```

## 🎯 What Works Today

### ✅ Fully Functional Features
- **Document Authenticity Analysis**: PDF/DOCX metadata analysis, file integrity checks
- **Contact Verification**: Email/phone validation with disposable domain detection
- **AI Content Detection**: Heuristic analysis (works without external APIs)
- **File Security Scanning**: Malicious content detection and validation
- **Structured Risk Assessment**: Multi-dimensional scoring with detailed rationale

### 🔧 Experimental Features
- **Background Verification**: Company/education verification (requires API keys)
- **Digital Footprint Analysis**: Social media presence verification (requires API keys)
- **AWS Bedrock AI Detection**: Advanced AI content detection (requires AWS credentials)

## 🛡️ Security Features

- **File Upload Security**: Strict MIME type validation, size limits (10MB max)
- **PII Protection**: Automatic redaction of sensitive data in logs
- **Input Validation**: Comprehensive validation of all inputs
- **Rate Limiting**: 60 requests per minute per client
- **Threat Model**: Documented security controls and attack mitigation

## 📊 Risk Scoring

The system provides multi-dimensional risk assessment:

### Risk Categories
- **AI Content** (35% weight): AI-generated content likelihood
- **Contact Info** (25% weight): Email/phone verification
- **Document Authenticity** (10% weight): File integrity and metadata
- **Background** (20% weight): Professional verification (when available)
- **Digital Footprint** (10% weight): Online presence consistency (when available)

### Scoring Scale
- **0-39%**: Low Risk (Green) - Legitimate candidate
- **40-69%**: Moderate Risk (Yellow) - Requires review
- **70-100%**: High Risk (Red) - Potential fraud indicators

## 🧪 Testing

### Run All Tests
```bash
cd python_backend
python3 run_tests.py
```

### Run Specific Test Types
```bash
# Unit tests only
python3 run_tests.py --type unit

# Integration tests
python3 run_tests.py --type integration

# With coverage report
python3 run_tests.py --coverage
```

## 🔧 Configuration

### Environment Variables (Optional)
The system works without external APIs using heuristic analysis. For enhanced functionality, set:

```bash
# AWS Configuration (for Bedrock AI detection)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Supabase Configuration (for data persistence)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# External API Keys (for enhanced verification)
NUMVERIFY_API_KEY=your_numverify_key
ABSTRACT_API_KEY=your_abstract_api_key
SERPAPI_KEY=your_serpapi_key
```

## 📁 Project Structure

```
ValidiaTakeHome/
├── samples/                      # Sample resumes for testing
│   ├── sample_resume_1.txt      # Software Engineer resume
│   ├── sample_resume_2.txt      # Marketing Manager resume
│   └── sample_resume_3.txt      # Data Scientist resume
├── python_backend/              # FastAPI backend
│   ├── main.py                  # Main FastAPI application
│   ├── detectors/               # Detection modules
│   ├── orchestrator/            # Analysis orchestration
│   ├── models/                  # Pydantic schemas
│   ├── utils/                   # Utilities and configuration
│   └── tests/                   # Test suite (97 tests)
├── app/                         # Next.js frontend
├── Dockerfile                   # Python 3.11+ container
├── docker-compose.yml           # Multi-service setup
└── README_COMPLETE.md           # This file
```

## 🚀 Deployment

### Production Docker Build
```bash
# Build the production image
docker build -t sentinelhire-api .

# Run the container
docker run -p 8000:8000 sentinelhire-api
```

### Frontend Deployment (Vercel)
```bash
# Build and deploy
pnpm build
vercel --prod
```

## 🔍 API Endpoints

### Main Endpoints
- `POST /analyze` - Comprehensive resume analysis
- `POST /ai-detect` - AI content detection only
- `POST /document-authenticity` - Document analysis only
- `POST /contact-verify` - Contact verification only

### Utility Endpoints
- `GET /health` - Health check
- `GET /cache/stats` - Cache statistics
- `POST /cache/clear` - Clear cache
- `GET /docs` - API documentation

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Kill processes on ports 3000 and 8000
   lsof -ti:3000,8000 | xargs kill -9
   ```

2. **Missing dependencies**
   ```bash
   # Reinstall frontend dependencies
   rm -rf node_modules pnpm-lock.yaml
   pnpm install
   
   # Reinstall Python dependencies
   cd python_backend
   pip install -r requirements.txt
   ```

3. **File upload errors**
   - Ensure file is PDF or DOCX format
   - Check file size is under 10MB
   - Verify file is not corrupted

## 📈 Performance

- **File Processing**: ~2-5 seconds for typical resume
- **Heuristic AI Analysis**: ~1-2 seconds
- **API Response**: <500ms for cached requests
- **Concurrent Users**: 60 requests/minute (configurable)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Run the test suite: `python3 run_tests.py`
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

---

**Built with ❤️ using Next.js, FastAPI, and comprehensive fraud detection algorithms**
