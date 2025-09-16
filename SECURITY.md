# Security Threat Model

## Overview

This document outlines the security threat model for the SentinelHire Resume Fraud Detection System, identifying potential attack vectors and mitigation strategies.

## System Architecture

The system consists of:
- **Frontend**: Next.js application (Port 3000)
- **Backend**: FastAPI application (Port 8000)
- **Database**: Supabase PostgreSQL
- **External APIs**: AWS Bedrock, various verification services
- **File Processing**: PDF/DOCX analysis

## Threat Vectors

### 1. File Upload Attacks

#### 1.1 Malicious File Uploads
**Threat**: Attackers upload malicious files to compromise the system.

**Attack Scenarios**:
- Executable files disguised as documents
- Malicious PDFs with embedded JavaScript
- DOCX files with malicious macros
- Zip bombs (compressed files that expand to enormous sizes)

**Mitigations**:
- Strict file type validation (PDF/DOCX only)
- Content-type verification against file signatures
- File size limits (10MB maximum)
- File security scanning for malicious content
- Sandboxed file processing environment

#### 1.2 SSRF (Server-Side Request Forgery)
**Threat**: Malicious files could trigger requests to internal services.

**Attack Scenarios**:
- PDFs with embedded URLs that trigger internal requests
- DOCX files with external references to internal services

**Mitigations**:
- Network isolation for file processing
- No external network access during file analysis
- Content sanitization before processing

### 2. Data Exfiltration

#### 2.1 PII Exposure
**Threat**: Sensitive candidate information exposed in logs or responses.

**Attack Scenarios**:
- PII logged in plain text
- PII included in error messages
- PII cached in memory

**Mitigations**:
- PII redaction in all log outputs
- Structured logging with automatic PII detection
- No PII in error messages
- Memory clearing after processing

#### 2.2 API Key Exposure
**Threat**: API keys and secrets exposed in logs or responses.

**Attack Scenarios**:
- Secrets logged during debugging
- API keys in error messages
- Secrets in version control

**Mitigations**:
- Environment variable management
- No secrets in logs
- Secret rotation capabilities
- .gitignore for sensitive files

### 3. Denial of Service (DoS)

#### 3.1 Resource Exhaustion
**Threat**: Attackers consume system resources to deny service.

**Attack Scenarios**:
- Large file uploads
- Rapid API requests
- Memory-intensive file processing

**Mitigations**:
- File size limits (10MB)
- Rate limiting (60 requests/minute)
- Memory limits for file processing
- Request timeout handling

#### 3.2 Zip Bomb Attacks
**Threat**: Compressed files that expand to enormous sizes.

**Attack Scenarios**:
- DOCX files with compressed content that expands to GB
- Nested compression layers

**Mitigations**:
- File size validation before decompression
- Maximum expansion ratio limits
- Timeout for file processing operations

### 4. Injection Attacks

#### 4.1 Code Injection
**Threat**: Malicious code execution through file content.

**Attack Scenarios**:
- JavaScript in PDFs
- VBA macros in DOCX files
- Script execution through file processing

**Mitigations**:
- No script execution during file processing
- Content sanitization
- Sandboxed processing environment

#### 4.2 SQL Injection
**Threat**: Malicious SQL through input parameters.

**Attack Scenarios**:
- SQL injection through candidate hints
- Database queries with user input

**Mitigations**:
- Parameterized queries
- Input validation and sanitization
- ORM usage (Supabase client)

### 5. Authentication and Authorization

#### 5.1 Unauthorized Access
**Threat**: Access to system without proper authentication.

**Attack Scenarios**:
- Direct API access without authentication
- Admin endpoint access

**Mitigations**:
- API key validation
- Admin endpoint protection
- Rate limiting per client

### 6. External Service Attacks

#### 6.1 API Abuse
**Threat**: Abuse of external APIs through the service.

**Attack Scenarios**:
- Excessive API calls to external services
- Malicious requests to verification APIs

**Mitigations**:
- API rate limiting
- Request caching
- Input validation before external calls

## Security Controls

### File Upload Security
- **File Type Validation**: Only PDF and DOCX files allowed
- **Content-Type Verification**: MIME type must match file extension
- **File Size Limits**: 10MB maximum file size
- **File Signature Validation**: File content must match extension
- **Malicious Content Scanning**: Detection of embedded scripts and executables

### Data Protection
- **PII Redaction**: Automatic redaction of PII in logs
- **Encryption**: All data encrypted in transit (HTTPS)
- **Access Controls**: API key-based authentication
- **Audit Logging**: Comprehensive logging of all operations

### Network Security
- **CORS Configuration**: Restricted to known origins
- **Rate Limiting**: 60 requests per minute per client
- **Request Validation**: All inputs validated and sanitized
- **Error Handling**: No sensitive information in error messages

### Operational Security
- **Secret Management**: Environment variables for all secrets
- **Regular Updates**: Dependencies kept up to date
- **Monitoring**: Comprehensive logging and monitoring
- **Backup and Recovery**: Regular database backups

## Incident Response

### Security Incident Procedures
1. **Detection**: Automated monitoring and alerting
2. **Containment**: Immediate isolation of affected systems
3. **Investigation**: Detailed analysis of the incident
4. **Recovery**: System restoration and validation
5. **Lessons Learned**: Post-incident review and improvements

### Contact Information
- **Security Team**: security@company.com
- **Emergency Contact**: +1-XXX-XXX-XXXX
- **Incident Response**: incident@company.com

## Compliance

### Data Protection Regulations
- **GDPR**: European data protection compliance
- **CCPA**: California consumer privacy compliance
- **SOC 2**: Security and availability controls

### Data Retention
- **Analysis Results**: Retained for 90 days
- **Logs**: Retained for 30 days
- **Personal Data**: Deleted after analysis completion

## Regular Security Reviews

### Monthly Reviews
- Security log analysis
- Vulnerability assessment
- Access control review

### Quarterly Reviews
- Threat model updates
- Security control effectiveness
- Incident response testing

### Annual Reviews
- Complete security audit
- Penetration testing
- Security training updates

---

**Last Updated**: January 2025
**Next Review**: February 2025
**Document Owner**: Security Team