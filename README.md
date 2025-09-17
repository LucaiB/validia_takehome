# SentinelHire - AI-Powered Resume Fraud Detection System

A comprehensive fraud detection system that analyzes resumes for authenticity, verifies candidate information, and provides multi-dimensional risk assessment using AI and external APIs.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and pnpm
- Python 3.9+
- Supabase account (optional)
- AWS account (for Bedrock AI detection)
- Optional: Redis (for caching)

### Option 1: Automated Setup (Recommended)

Use the provided setup script for the fastest start:

```bash
# Clone the repository
git clone https://github.com/LucaiB/validia_takehome.git
cd validia_takehome

# Run the automated setup script
chmod +x setup.sh
./setup.sh
```

The setup script will:
- ✅ Install frontend dependencies (`pnpm install`)
- ✅ Create Python virtual environment
- ✅ Install Python dependencies
- ✅ Set up environment files from examples
- ✅ Start both backend and frontend services

### Option 2: Docker (Recommended for Production)

```bash
# Clone the repository
git clone https://github.com/LucaiB/validia_takehome.git
cd validia_takehome

# Build and run with Docker Compose
docker-compose up --build

# The API will be available at http://localhost:8000
# The frontend will be available at http://localhost:3000
```

### Option 3: Manual Local Development

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

## 🔧 Environment Configuration

### Frontend Environment (`.env.local`)
```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Python API URL (default: http://localhost:8000)
PYTHON_API_URL=http://localhost:8000
```

### Backend Environment (`.env` in `python_backend/`)
```bash
# AWS Configuration (Required for AI detection)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Supabase Configuration (Optional - for future database features)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# External API Keys (Optional - enhances functionality)
NUMVERIFY_API_KEY=your_numverify_key
ABSTRACT_API_KEY=your_abstract_api_key
SERPAPI_KEY=your_serpapi_key

# Background Verification APIs (Optional - all free)
COLLEGE_SCORECARD_KEY=your_college_scorecard_key
GITHUB_TOKEN=your_github_token
SEC_CONTACT_EMAIL=you@example.com
OPENALEX_CONTACT_EMAIL=you@example.com

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=60
MAX_FILE_SIZE_MB=10
```

## 🎯 Features

### ✅ Core Detection Capabilities (Production Ready)
- **AI Content Detection**: Uses Amazon Bedrock (Claude Sonnet 4) to detect AI-generated content
- **Document Authenticity**: Deep analysis of PDF/DOCX metadata, structure, and integrity
- **Contact Verification**: Email/phone validation with geo-consistency checks
- **Background Verification**: Company, education, and timeline verification using public APIs
- **Digital Footprint Analysis**: Professional presence verification across platforms
- **File Security Scanning**: Malicious file detection and security validation

### ✅ Technical Features (Production Ready)
- **Multi-format Support**: PDF and DOCX resume processing
- **Real-time Analysis**: Fast processing with comprehensive caching
- **Rate Limiting**: Built-in protection against abuse
- **Comprehensive Testing**: 97 unit tests with 100% pass rate
- **Modern Architecture**: Next.js frontend + FastAPI backend

### 🔄 Future Enhancements (In Development)
- **Admin Dashboard**: Candidate management and analysis review interface
- **Database Integration**: Full Supabase integration for data persistence
- **Advanced Analytics**: Historical analysis and trend reporting
- **Bulk Processing**: Batch resume analysis capabilities

## 🏗️ Architecture

### System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI       │    │   External      │
│   Frontend      │◄──►│   Backend       │◄──►│   APIs          │
│   (Port 3000)   │    │   (Port 8000)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Supabase      │    │   Redis Cache   │    │   AWS Bedrock   │
│   Database      │    │   (Optional)    │    │   AI Service    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Frontend (Next.js)
- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS
- **File Processing**: PDF/DOCX parsing with mammoth and pdf-parse
- **State Management**: React hooks with local state
- **API Integration**: RESTful API calls to Python backend

### Backend (FastAPI)
- **Framework**: FastAPI with async/await support
- **AI Integration**: Amazon Bedrock (Claude Sonnet 4)
- **Document Processing**: PyPDF2, python-docx, pdfplumber
- **External APIs**: NumVerify, Abstract API, SerpAPI, GLEIF, SEC EDGAR, OpenAlex, GitHub, College Scorecard
- **Caching**: In-memory cache with TTL
- **Rate Limiting**: Sliding window algorithm
- **Security**: File scanning and validation

## 📁 Project Structure

```
ValidiaTakeHome/
├── app/                          # Next.js frontend
│   ├── api/                      # API routes (proxy to Python backend)
│   │   ├── upload-analyze/       # Main analysis endpoint
│   │   ├── ai-analysis/          # AI analysis endpoint
│   │   └── admin/                # Admin endpoints
│   ├── page.tsx                  # Main dashboard UI
│   └── globals.css               # Global styles
├── python_backend/               # FastAPI backend
│   ├── app/                      # FastAPI application
│   │   ├── main.py              # Main FastAPI app
│   │   ├── contact_verification.py
│   │   ├── background_verification.py
│   │   └── digital_footprint.py
│   ├── detectors/                # Detection modules
│   │   ├── ai_text.py           # AI content detection
│   │   ├── document_auth.py     # Document authenticity
│   │   ├── contact_verification.py
│   │   ├── digital_footprint.py
│   │   └── file_security.py     # Security scanning
│   ├── background_verification/  # Background check sources
│   │   ├── sources/             # External API integrations
│   │   ├── logic.py             # Verification orchestration
│   │   └── scoring.py           # Scoring algorithms
│   ├── orchestrator/            # Main analysis orchestrator
│   │   └── analyzer.py          # Core analysis logic
│   ├── models/                  # Pydantic schemas
│   ├── utils/                   # Utilities (config, caching, logging)
│   ├── tests/                   # Comprehensive test suite
│   │   ├── unit/                # Unit tests (97 tests)
│   │   ├── integration/         # Integration tests
│   │   └── contract/            # API contract tests
│   └── requirements.txt         # Python dependencies
├── supabase/                    # Database schema and migrations
├── setup.sh                     # Automated setup script
└── README.md                    # This file
```

## 🔧 API Usage

### Main Analysis Endpoint
```bash
# Analyze a resume file
curl -F file=@samples/sample_resume.pdf http://localhost:8000/analyze | jq
```

### Sample Request/Response

**Request:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@samples/sample_resume.pdf" \
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
    "model": "claude-sonnet-4",
    "rationale": "Heuristic analysis suggests human-written content"
  },
  "documentAuthenticity": {
    "fileName": "sample_resume.pdf",
    "fileSize": 1024,
    "fileType": "application/pdf",
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
  "backgroundVerification": {
    "company_evidence": {...},
    "education_evidence": {...},
    "developer_evidence": {...},
    "timeline_assessment": {...},
    "score": {"composite": 0.75}
  },
  "digitalFootprint": {
    "social_presence": {...},
    "search_results": [...],
    "consistency_score": 89
  },
  "aggregatedReport": {
    "overall_score": 35,
    "weights_applied": {
      "ai_content": 0.35,
      "contact_info": 0.25,
      "background": 0.20,
      "digital_footprint": 0.10,
      "document_authenticity": 0.10
    },
    "slices": [...],
    "evidence": {...},
    "rationale": [...],
    "generated_at": "2025-01-16T18:00:00Z",
    "version": "1.0.0"
  }
}
```

## 🔍 API Endpoints

### Main Analysis Endpoints
```http
POST /analyze                    # Comprehensive resume analysis
POST /ai-detect                  # AI content detection only
POST /document-authenticity      # Document analysis only
POST /contact-verify             # Contact verification only
POST /background-verify          # Background verification only
POST /digital-footprint          # Digital footprint analysis only
```

### Utility Endpoints
```http
GET /health                      # Health check
GET /cache/stats                 # Cache statistics
POST /cache/clear                # Clear cache
GET /test-rate-limit             # Rate limit testing
GET /docs                        # API documentation
```

## 📊 Risk Scoring System

The system provides comprehensive multi-dimensional risk assessment with detailed scoring algorithms:

### Overall Risk Calculation
The final risk score is calculated by inverting verification scores and applying weighted averages:

```python
# Risk = 100 - (Weighted Average of Verification Scores)
overall_risk = 100 - (
    0.35 * ai_verification_score +
    0.25 * contact_verification_score + 
    0.20 * background_verification_score +
    0.10 * digital_footprint_score +
    0.10 * document_authenticity_score
)
```

### Individual Component Scoring

#### 1. AI Content Detection (35% weight)
- **Score Range**: 0-100 (confidence percentage)
- **Method**: Amazon Bedrock Claude Sonnet 4 analysis
- **Factors**: Content patterns, language complexity, experience descriptions
- **Risk Inversion**: Higher confidence = Lower risk

#### 2. Contact Verification (25% weight)
- **Score Range**: 0-100 (composite verification score)
- **Components**:
  - **Email Verification** (40%): Syntax validation, MX records, disposable detection
  - **Phone Verification** (40%): Format validation, carrier lookup, toll-free detection
  - **Geo Consistency** (20%): Location matching between phone and stated location
- **Calculation**: `(email_score * 0.4) + (phone_score * 0.4) + (geo_score * 0.2)`

#### 3. Background Verification (20% weight)
- **Score Range**: 0-100 (composite verification score)
- **Components**:
  - **Company Identity** (40%): GLEIF, SEC EDGAR, OpenCorporates verification
  - **Education** (20%): College Scorecard, OpenAlex institution verification
  - **Timeline** (25%): Employment timeline consistency via Wayback Machine
  - **Developer Footprint** (15%): GitHub profile analysis (additive scoring)
- **Developer Scoring** (Additive System):
  - No GitHub: 0% (neutral, no penalty)
  - GitHub Profile: +30% (basic presence)
  - 5+ Repositories: +20% (active development)
  - 10+ Public Repos: +10% (high activity)
  - **Maximum**: 60% (normalized to 100% in composite)

#### 4. Digital Footprint Analysis (10% weight)
- **Score Range**: 0-100 (consistency score)
- **Method**: SerpAPI search results analysis
- **Factors**: Professional presence, LinkedIn profiles, search result consistency
- **Sources**: Google search, LinkedIn, GitHub, professional platforms

#### 5. Document Authenticity (10% weight)
- **Score Range**: 0-100 (authenticity score)
- **PDF Analysis**: Metadata, fonts, structure, JavaScript detection
- **DOCX Analysis**: Metadata, fonts, macros, embedded content
- **Security Checks**: File integrity, suspicious patterns, malicious content

### Risk Categories
- **0-39%**: Low Risk (Green) - Legitimate candidate with strong verification
- **40-69%**: Moderate Risk (Yellow) - Some concerns, requires review
- **70-100%**: High Risk (Red) - Multiple fraud indicators detected

### Score Normalization
- All component scores are normalized to 0-100 scale
- Developer scores (0-60) are normalized to 0-100 for composite calculation
- Final risk score represents likelihood of fraud (higher = more risky)

## 🧪 Testing

The project includes a comprehensive test suite with 97 unit tests achieving 100% pass rate.

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

### Test Categories
- **File Security**: 20 tests - Malicious file detection
- **AI Detection**: 12 tests - Content analysis
- **Contact Verification**: 13 tests - Email/phone validation
- **Document Authenticity**: 15 tests - Metadata analysis
- **Digital Footprint**: 11 tests - Online presence verification
- **Background Sources**: 23 tests - External API integrations
- **Cached API Client**: 5 tests - Caching functionality

## 🛡️ Security Features

### File Security
- Malicious file detection and blocking
- File type validation and MIME type checking
- Size limit enforcement (10MB max)
- Content pattern analysis

### API Security
- Rate limiting (60 requests/minute default)
- Input validation and sanitization
- Error handling without information leakage
- CORS configuration

### Data Privacy
- No PII storage in logs
- Secure API key management
- Configurable data retention

## 🔧 Configuration

### Environment Variables
All configuration is managed through environment variables. See `python_backend/env.example` for complete list.

### Rate Limiting
- **Default**: 60 requests per minute per client
- **Configurable**: Via `RATE_LIMIT_PER_MINUTE` environment variable
- **Algorithm**: Sliding window with Redis backend

### Caching
- **API Responses**: TTL-based caching for external API calls
- **Analysis Results**: Cached to avoid re-processing
- **Configurable**: TTL and cache size limits

## 🚀 Deployment

### Frontend (Vercel)
```bash
# Build and deploy
pnpm build
# Deploy to Vercel
vercel --prod
```

### Backend (Docker)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### Database (Supabase)
- Use Supabase cloud or self-hosted
- Run migrations: `npx supabase db push`
- Configure environment variables

## 📈 Performance

### Benchmarks
- **File Processing**: ~2-5 seconds for typical resume
- **AI Analysis**: ~1-3 seconds per analysis
- **API Response**: <500ms for cached requests
- **Concurrent Users**: 60 requests/minute (configurable)

### Optimization
- Comprehensive caching strategy
- Async/await throughout
- Connection pooling for external APIs
- Efficient file processing

## 🐛 Troubleshooting

### Common Issues

1. **Setup Script Fails**: 
   - Ensure you have Node.js 18+ and Python 3.9+ installed
   - Check that `pnpm` is installed: `npm install -g pnpm`
   - Try manual setup if script fails

2. **Port Conflicts**: 
   ```bash
   # Kill processes on ports 3000 and 8000
   lsof -ti:3000,8000 | xargs kill -9
   ```

3. **Missing Dependencies**:
   ```bash
   # Reinstall frontend dependencies
   rm -rf node_modules pnpm-lock.yaml
   pnpm install
   
   # Reinstall Python dependencies
   cd python_backend
   pip install -r requirements.txt
   ```

4. **File Upload Errors**:
   - Ensure file is PDF or DOCX format
   - Check file size is under 10MB
   - Verify file is not corrupted

5. **API Key Issues**: Verify environment variables are set correctly

6. **Rate Limiting**: Adjust `RATE_LIMIT_PER_MINUTE` if needed

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG
python3 main.py
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install dependencies
4. Run tests: `python3 run_tests.py`
5. Make changes and test
6. Submit pull request

### Code Quality
- 100% test coverage target
- Type hints throughout
- Async/await patterns
- Comprehensive error handling

## 🔮 Current Status & Future Roadmap

### Current Limitations
- **Admin Dashboard**: UI exists but backend API routes are not fully implemented
- **Database Integration**: Supabase schema is defined but not fully integrated with the application
- **Data Persistence**: Analysis results are not currently saved to database
- **Bulk Operations**: No support for processing multiple resumes simultaneously

### Phase 1 - Core Platform (Current Release)
- [x] Resume fraud detection engine
- [x] Multi-dimensional risk scoring
- [x] Real-time analysis capabilities
- [x] Comprehensive testing suite
- [x] Production-ready API endpoints
- [x] Automated AI analysis integration

### Phase 2 - Data Management (Next Release)
- [ ] Complete admin dashboard implementation
- [ ] Full database integration with Supabase
- [ ] Analysis result persistence
- [ ] Candidate management system
- [ ] Historical analysis tracking

### Phase 3 - Advanced Features (Future)
- [ ] OCR support for scanned documents
- [ ] Additional file format support
- [ ] Advanced analytics dashboard
- [ ] Batch processing capabilities
- [ ] API webhook support
- [ ] Enhanced security scanning

### Performance Improvements
- [ ] Redis clustering support
- [ ] Database query optimization
- [ ] CDN integration for static assets
- [ ] Horizontal scaling support

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For additional support or questions:
- Check the troubleshooting section above
- Review the API documentation at `http://localhost:8000/docs`
- Enable debug mode for detailed logging

---

**Built with ❤️ using Next.js, FastAPI, and Amazon Bedrock**