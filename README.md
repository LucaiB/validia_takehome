# SentinelHire - AI-Powered Resume Fraud Detection System

A comprehensive fraud detection system that analyzes resumes for authenticity, verifies candidate information, and provides multi-dimensional risk assessment using AI and external APIs.

## 🚀 Features

### Core Detection Capabilities
- **AI Content Detection**: Uses Amazon Bedrock (Claude Sonnet 4) to detect AI-generated content
- **Document Authenticity**: Deep analysis of PDF/DOCX metadata, structure, and integrity
- **Contact Verification**: Email/phone validation with geo-consistency checks
- **Background Verification**: Company, education, and timeline verification using public APIs
- **Digital Footprint Analysis**: Professional presence verification across platforms
- **File Security Scanning**: Malicious file detection and security validation

### Technical Features
- **Multi-format Support**: PDF and DOCX resume processing
- **Real-time Analysis**: Fast processing with comprehensive caching
- **Rate Limiting**: Built-in protection against abuse
- **Comprehensive Testing**: 97 unit tests with 100% pass rate
- **Modern Architecture**: Next.js frontend + FastAPI backend
- **Database Integration**: Supabase for data persistence

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

### Database (Supabase)
- **Candidates**: Store candidate information
- **Analyses**: Store analysis results and reports
- **Review History**: Audit trail for analysis reviews

## 📁 Project Structure

```
ValidiaTakeHome/
├── app/                          # Next.js frontend
│   ├── api/                      # API routes (proxy to Python backend)
│   │   ├── upload-analyze/       # Main analysis endpoint
│   │   ├── ai-detect/           # AI content detection
│   │   └── admin/               # Admin endpoints
│   ├── page.tsx                 # Main dashboard UI
│   └── globals.css              # Global styles
├── python_backend/              # FastAPI backend
│   ├── app/                     # FastAPI application
│   │   ├── main.py             # Main FastAPI app
│   │   ├── contact_verification.py
│   │   ├── background_verification.py
│   │   └── digital_footprint.py
│   ├── detectors/               # Detection modules
│   │   ├── ai_text.py          # AI content detection
│   │   ├── document_auth.py    # Document authenticity
│   │   ├── contact_verification.py
│   │   ├── digital_footprint.py
│   │   └── file_security.py    # Security scanning
│   ├── background_verification/ # Background check sources
│   │   ├── sources/            # External API integrations
│   │   ├── logic.py            # Verification orchestration
│   │   └── scoring.py          # Scoring algorithms
│   ├── orchestrator/           # Main analysis orchestrator
│   │   └── analyzer.py         # Core analysis logic
│   ├── models/                 # Pydantic schemas
│   ├── utils/                  # Utilities (config, caching, logging)
│   ├── tests/                  # Comprehensive test suite
│   │   ├── unit/               # Unit tests (97 tests)
│   │   ├── integration/        # Integration tests
│   │   └── contract/           # API contract tests
│   └── requirements.txt        # Python dependencies
├── supabase/                   # Database schema and migrations
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and pnpm
- Python 3.9+
- Supabase account
- AWS account (for Bedrock)
- Optional: Redis (for caching)

### 1. Clone and Install Dependencies

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
```

### 2. Environment Configuration

Create `.env.local` in the root directory:
```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Python API URL (default: http://localhost:8000)
PYTHON_API_URL=http://localhost:8000
```

Create `.env` in `python_backend/` (copy from `env.example`):
```bash
# AWS Configuration (Required)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Supabase Configuration (Required)
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

### 3. Database Setup

```bash
# Start Supabase locally (if using local development)
npx supabase start

# Or use Supabase cloud - run migrations
npx supabase db push
```

### 4. Start the Application

**Terminal 1 - Python Backend:**
```bash
cd python_backend
source venv/bin/activate
python3 main.py
```

**Terminal 2 - Next.js Frontend:**
```bash
pnpm dev
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔧 API Endpoints

### Main Analysis Endpoint
```http
POST /analyze
Content-Type: multipart/form-data

Parameters:
- file: PDF or DOCX resume file
- candidate_hints: Optional JSON with candidate information
```

### Individual Detection Endpoints
```http
POST /ai-detect          # AI content detection
POST /document-authenticity  # Document analysis
POST /contact-verify     # Contact verification
POST /background-verify  # Background verification
POST /digital-footprint  # Digital footprint analysis
```

### Utility Endpoints
```http
GET /health             # Health check
GET /cache/stats        # Cache statistics
POST /cache/clear       # Clear cache
GET /test-rate-limit    # Rate limit testing
```

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

## 🔍 Detection Capabilities

### 1. AI Content Detection
- **Model**: Amazon Bedrock Claude Sonnet 4
- **Features**: Confidence scoring, rationale generation
- **Coverage**: Text analysis, experience sections, skills descriptions

### 2. Document Authenticity
- **PDF Analysis**: Metadata, structure, fonts, images, JavaScript detection
- **DOCX Analysis**: Metadata, structure, fonts, macros detection
- **Security Checks**: File integrity, suspicious patterns, embedded content

### 3. Contact Verification
- **Email Validation**: Syntax, MX records, disposable email detection
- **Phone Validation**: Format, carrier, toll-free detection
- **Geo Consistency**: Location matching between phone and stated location

### 4. Background Verification
- **Company Verification**: GLEIF, SEC EDGAR, OpenCorporates
- **Education Verification**: College Scorecard, OpenAlex
- **Timeline Verification**: Wayback Machine, GitHub activity
- **Developer Footprint**: GitHub profile analysis

### 5. Digital Footprint Analysis
- **Search Engine Queries**: Google search via SerpAPI
- **Professional Presence**: LinkedIn, GitHub, Google Scholar
- **Consistency Scoring**: Cross-platform verification

### 6. File Security Scanning
- **Malicious File Detection**: JavaScript, embedded executables
- **File Type Validation**: MIME type verification
- **Size Limits**: Configurable file size restrictions
- **Content Analysis**: Suspicious pattern detection

## 📊 Risk Scoring

The system provides multi-dimensional risk assessment:

### Risk Categories
- **AI Content** (35% weight): AI-generated content likelihood
- **Contact Info** (25% weight): Email/phone verification
- **Background** (20% weight): Professional verification
- **Digital Footprint** (10% weight): Online presence consistency
- **Document Authenticity** (10% weight): File integrity and metadata

### Scoring Scale
- **0-39%**: Low Risk (Green)
- **40-69%**: Moderate Risk (Yellow)
- **70-100%**: High Risk (Red)

## 🛡️ Security Features

### File Security
- Malicious file detection and blocking
- File type validation and MIME type checking
- Size limit enforcement
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

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed
2. **API Key Issues**: Verify environment variables are set
3. **File Upload Errors**: Check file type and size limits
4. **Rate Limiting**: Adjust `RATE_LIMIT_PER_MINUTE` if needed

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG
python3 main.py
```

## 🔮 Roadmap

### Planned Features
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

---

**Built with ❤️ using Next.js, FastAPI, and Amazon Bedrock**