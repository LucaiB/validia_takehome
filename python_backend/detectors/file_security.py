"""
File security scanner for detecting malicious files and security threats.
"""

import os
import hashlib
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import re
from utils.logging_config import get_logger

logger = get_logger(__name__)

class FileSecurityScanner:
    """Comprehensive file security scanner for detecting threats."""
    
    def __init__(self):
        """Initialize the file security scanner."""
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        self.suspicious_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
            '.ps1', '.sh', '.py', '.php', '.asp', '.jsp', '.aspx', '.pl', '.rb',
            '.dll', '.sys', '.drv', '.ocx', '.cpl', '.msi', '.msp', '.mst'
        }
        
        # Suspicious file signatures (magic numbers)
        self.suspicious_signatures = {
            b'MZ': 'PE executable',
            b'\x7fELF': 'ELF executable',
            b'\xca\xfe\xba\xbe': 'Java class file',
            b'PK\x03\x04': 'ZIP/Office document',
            b'%PDF': 'PDF document',
            b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1': 'Microsoft Office document',
        }
        
        # Suspicious patterns in file content
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'eval\s*\(',
            r'exec\s*\(',
            r'system\s*\(',
            r'shell_exec\s*\(',
            r'passthru\s*\(',
            r'file_get_contents\s*\(',
            r'fopen\s*\(',
            r'fwrite\s*\(',
            r'fputs\s*\(',
            r'include\s*\(',
            r'require\s*\(',
            r'require_once\s*\(',
            r'include_once\s*\(',
        ]
        
        # Suspicious macro patterns for Office documents
        self.macro_patterns = [
            r'Sub\s+\w+',
            r'Function\s+\w+',
            r'Private\s+Sub',
            r'Public\s+Sub',
            r'Private\s+Function',
            r'Public\s+Function',
            r'Dim\s+\w+',
            r'Set\s+\w+',
            r'Call\s+\w+',
            r'Application\.',
            r'ActiveDocument\.',
            r'ActiveWorkbook\.',
            r'CreateObject\s*\(',
            r'GetObject\s*\(',
            r'Shell\s*\(',
            r'Run\s*\(',
        ]

    async def scan_file(self, file_path: str, file_content: bytes) -> Dict[str, Any]:
        """
        Perform comprehensive security scan on uploaded file.
        
        Args:
            file_path: Path to the file
            file_content: File content as bytes
            
        Returns:
            Security scan results
        """
        logger.info(f"Starting security scan for file: {file_path}")
        
        results = {
            "is_safe": True,
            "threats_detected": [],
            "warnings": [],
            "file_info": {},
            "scan_details": {}
        }
        
        try:
            # Basic file information
            file_info = self._get_file_info(file_path, file_content)
            results["file_info"] = file_info
            
            # Size check
            if file_info["size"] > self.max_file_size:
                results["is_safe"] = False
                results["threats_detected"].append({
                    "type": "file_size",
                    "severity": "high",
                    "message": f"File size ({file_info['size']} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)"
                })
            
            # File extension check
            ext_threat = self._check_file_extension(file_path)
            if ext_threat:
                results["threats_detected"].append(ext_threat)
                results["is_safe"] = False
            
            # File signature check
            sig_threat = self._check_file_signature(file_content)
            if sig_threat:
                results["threats_detected"].append(sig_threat)
                results["is_safe"] = False
            
            # Content analysis
            content_threats = await self._analyze_content(file_content, file_path)
            results["threats_detected"].extend(content_threats)
            
            # PDF-specific security checks
            if file_info["mime_type"] == "application/pdf":
                pdf_threats = self._scan_pdf_security(file_content)
                results["threats_detected"].extend(pdf_threats)
            
            # Office document security checks
            elif file_info["mime_type"] in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                          "application/msword",
                                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                          "application/vnd.ms-excel"]:
                office_threats = self._scan_office_security(file_content, file_path)
                results["threats_detected"].extend(office_threats)
            
            # ZIP-based file checks
            if file_info["mime_type"] == "application/zip":
                zip_threats = self._scan_zip_security(file_content)
                results["threats_detected"].extend(zip_threats)
            
            # Update safety status based on threats
            if results["threats_detected"]:
                high_severity = any(t.get("severity") == "high" for t in results["threats_detected"])
                if high_severity:
                    results["is_safe"] = False
                else:
                    results["warnings"].extend([t for t in results["threats_detected"] if t.get("severity") == "medium"])
            
            # Generate scan summary
            results["scan_details"] = {
                "total_checks": 8,
                "threats_found": len(results["threats_detected"]),
                "warnings_found": len(results["warnings"]),
                "file_hash": file_info["sha256"],
                "scan_timestamp": file_info["scan_time"]
            }
            
            logger.info(f"Security scan completed for {file_path}: {'SAFE' if results['is_safe'] else 'THREATS DETECTED'}")
            return results
            
        except Exception as e:
            logger.error(f"Security scan failed for {file_path}: {e}")
            results["is_safe"] = False
            results["threats_detected"].append({
                "type": "scan_error",
                "severity": "high",
                "message": f"Security scan failed: {str(e)}"
            })
            return results

    def _get_file_info(self, file_path: str, file_content: bytes) -> Dict[str, Any]:
        """Get basic file information."""
        try:
            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_name)[1].lower()
            
            # Detect MIME type based on file extension and content
            mime_type = self._detect_mime_type(file_content, file_extension)
            
            # Calculate file hash
            sha256_hash = hashlib.sha256(file_content).hexdigest()
            
            return {
                "name": file_name,
                "extension": file_extension,
                "size": len(file_content),
                "mime_type": mime_type,
                "sha256": sha256_hash,
                "scan_time": str(os.path.getctime(file_path)) if os.path.exists(file_path) else "unknown"
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {
                "name": "unknown",
                "extension": "",
                "size": len(file_content),
                "mime_type": "application/octet-stream",
                "sha256": hashlib.sha256(file_content).hexdigest(),
                "scan_time": "unknown"
            }

    def _detect_mime_type(self, file_content: bytes, file_extension: str) -> str:
        """Detect MIME type based on file extension and content signatures."""
        # Check file signatures first
        if file_content.startswith(b'%PDF'):
            return "application/pdf"
        elif file_content.startswith(b'PK\x03\x04'):
            # Could be ZIP, DOCX, XLSX, PPTX, etc.
            if file_extension in ['.docx']:
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif file_extension in ['.xlsx']:
                return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif file_extension in ['.pptx']:
                return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            else:
                return "application/zip"
        elif file_content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
            # Microsoft Office document
            if file_extension in ['.doc']:
                return "application/msword"
            elif file_extension in ['.xls']:
                return "application/vnd.ms-excel"
            elif file_extension in ['.ppt']:
                return "application/vnd.ms-powerpoint"
            else:
                return "application/vnd.ms-office"
        elif file_content.startswith(b'MZ'):
            return "application/x-msdownload"  # PE executable
        elif file_content.startswith(b'\x7fELF'):
            return "application/x-executable"  # ELF executable
        elif file_content.startswith(b'\xca\xfe\xba\xbe'):
            return "application/java-vm"  # Java class file
        
        # Fall back to extension-based detection
        extension_mime_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.txt': 'text/plain',
            '.rtf': 'application/rtf',
            '.zip': 'application/zip',
            '.exe': 'application/x-msdownload',
            '.bat': 'application/x-msdownload',
            '.cmd': 'application/x-msdownload',
            '.com': 'application/x-msdownload',
            '.pif': 'application/x-msdownload',
            '.scr': 'application/x-msdownload',
            '.vbs': 'application/x-msdownload',
            '.js': 'application/javascript',
            '.jar': 'application/java-archive',
            '.ps1': 'application/x-powershell',
            '.sh': 'application/x-sh',
            '.py': 'text/x-python',
            '.php': 'application/x-php',
            '.asp': 'application/x-asp',
            '.jsp': 'application/x-jsp',
            '.aspx': 'application/x-aspx',
            '.pl': 'application/x-perl',
            '.rb': 'application/x-ruby',
            '.dll': 'application/x-msdownload',
            '.sys': 'application/x-msdownload',
            '.drv': 'application/x-msdownload',
            '.ocx': 'application/x-msdownload',
            '.cpl': 'application/x-msdownload',
            '.msi': 'application/x-msdownload',
            '.msp': 'application/x-msdownload',
            '.mst': 'application/x-msdownload',
        }
        
        return extension_mime_map.get(file_extension, "application/octet-stream")

    def _check_file_extension(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Check if file extension is suspicious."""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in self.suspicious_extensions:
            return {
                "type": "suspicious_extension",
                "severity": "high",
                "message": f"File has suspicious extension: {file_extension}"
            }
        return None

    def _check_file_signature(self, file_content: bytes) -> Optional[Dict[str, Any]]:
        """Check file signature for suspicious patterns."""
        for signature, description in self.suspicious_signatures.items():
            if file_content.startswith(signature):
                if signature in [b'MZ', b'\x7fELF', b'\xca\xfe\xba\xbe']:
                    return {
                        "type": "executable_signature",
                        "severity": "high",
                        "message": f"File has executable signature: {description}"
                    }
        return None

    async def _analyze_content(self, file_content: bytes, file_path: str) -> List[Dict[str, Any]]:
        """Analyze file content for suspicious patterns."""
        threats = []
        
        try:
            # Convert to string for pattern matching
            content_str = file_content.decode('utf-8', errors='ignore')
            
            # Check for suspicious patterns
            for pattern in self.suspicious_patterns:
                matches = re.findall(pattern, content_str, re.IGNORECASE | re.DOTALL)
                if matches:
                    threats.append({
                        "type": "suspicious_content",
                        "severity": "medium",
                        "message": f"Found suspicious pattern: {pattern}",
                        "matches_count": len(matches)
                    })
            
            # Check for embedded scripts
            script_tags = re.findall(r'<script[^>]*>.*?</script>', content_str, re.IGNORECASE | re.DOTALL)
            if script_tags:
                threats.append({
                    "type": "embedded_script",
                    "severity": "high",
                    "message": f"Found {len(script_tags)} embedded script tags",
                    "matches_count": len(script_tags)
                })
            
            # Check for data URIs
            data_uris = re.findall(r'data:[^;]+;base64,', content_str, re.IGNORECASE)
            if data_uris:
                threats.append({
                    "type": "data_uri",
                    "severity": "medium",
                    "message": f"Found {len(data_uris)} data URIs (potential embedded content)",
                    "matches_count": len(data_uris)
                })
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            threats.append({
                "type": "content_analysis_error",
                "severity": "low",
                "message": f"Content analysis failed: {str(e)}"
            })
        
        return threats

    def _scan_pdf_security(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Scan PDF files for security threats."""
        threats = []
        
        try:
            content_str = file_content.decode('utf-8', errors='ignore')
            
            # Check for JavaScript in PDF
            js_patterns = [
                r'/JS\s+',
                r'/JavaScript\s+',
                r'/OpenAction\s+',
                r'/AA\s+',
                r'/Launch\s+',
                r'/GoToR\s+',
                r'/SubmitForm\s+',
                r'/ImportData\s+',
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, content_str, re.IGNORECASE)
                if matches:
                    threats.append({
                        "type": "pdf_javascript",
                        "severity": "high",
                        "message": f"PDF contains potentially malicious JavaScript: {pattern}",
                        "matches_count": len(matches)
                    })
            
            # Check for embedded files
            embedded_patterns = [
                r'/EmbeddedFile',
                r'/FileAttachment',
                r'/F\s+\([^)]*\.(exe|bat|cmd|com|pif|scr|vbs|js|jar|ps1|sh|py|php|asp|jsp|aspx|pl|rb|dll|sys|drv|ocx|cpl|msi|msp|mst)',
            ]
            
            for pattern in embedded_patterns:
                matches = re.findall(pattern, content_str, re.IGNORECASE)
                if matches:
                    threats.append({
                        "type": "pdf_embedded_file",
                        "severity": "high",
                        "message": f"PDF contains embedded files: {pattern}",
                        "matches_count": len(matches)
                    })
            
        except Exception as e:
            logger.error(f"Error scanning PDF security: {e}")
        
        return threats

    def _scan_office_security(self, file_content: bytes, file_path: str) -> List[Dict[str, Any]]:
        """Scan Office documents for security threats."""
        threats = []
        
        try:
            # For DOCX files, check for macros
            if file_path.lower().endswith('.docx'):
                threats.extend(self._scan_docx_macros(file_content))
            elif file_path.lower().endswith('.doc'):
                threats.extend(self._scan_doc_macros(file_content))
            
        except Exception as e:
            logger.error(f"Error scanning Office security: {e}")
        
        return threats

    def _scan_docx_macros(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Scan DOCX files for macros."""
        threats = []
        
        try:
            with zipfile.ZipFile(io.BytesIO(file_content)) as zip_file:
                # Check for macro files
                macro_files = [name for name in zip_file.namelist() if 'vbaProject.bin' in name or 'macros' in name.lower()]
                
                if macro_files:
                    threats.append({
                        "type": "office_macro",
                        "severity": "high",
                        "message": f"DOCX contains macro files: {macro_files}",
                        "matches_count": len(macro_files)
                    })
                
                # Check for embedded objects
                embedded_files = [name for name in zip_file.namelist() if 'embeddings' in name.lower()]
                if embedded_files:
                    threats.append({
                        "type": "office_embedded",
                        "severity": "medium",
                        "message": f"DOCX contains embedded files: {embedded_files}",
                        "matches_count": len(embedded_files)
                    })
        
        except Exception as e:
            logger.error(f"Error scanning DOCX macros: {e}")
        
        return threats

    def _scan_doc_macros(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Scan DOC files for macros."""
        threats = []
        
        try:
            content_str = file_content.decode('utf-8', errors='ignore')
            
            # Check for macro patterns
            for pattern in self.macro_patterns:
                matches = re.findall(pattern, content_str, re.IGNORECASE)
                if matches:
                    threats.append({
                        "type": "office_macro",
                        "severity": "high",
                        "message": f"DOC contains macro code: {pattern}",
                        "matches_count": len(matches)
                    })
        
        except Exception as e:
            logger.error(f"Error scanning DOC macros: {e}")
        
        return threats

    def _scan_zip_security(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Scan ZIP files for security threats."""
        threats = []
        
        try:
            with zipfile.ZipFile(io.BytesIO(file_content)) as zip_file:
                file_list = zip_file.namelist()
                
                # Check for suspicious files in ZIP
                suspicious_files = [name for name in file_list if any(name.lower().endswith(ext) for ext in self.suspicious_extensions)]
                
                if suspicious_files:
                    threats.append({
                        "type": "zip_suspicious_files",
                        "severity": "high",
                        "message": f"ZIP contains suspicious files: {suspicious_files}",
                        "matches_count": len(suspicious_files)
                    })
                
                # Check for path traversal attacks
                path_traversal = [name for name in file_list if '..' in name or name.startswith('/')]
                if path_traversal:
                    threats.append({
                        "type": "zip_path_traversal",
                        "severity": "high",
                        "message": f"ZIP contains path traversal attempts: {path_traversal}",
                        "matches_count": len(path_traversal)
                    })
                
                # Check for nested ZIP files (zip bombs)
                nested_zips = [name for name in file_list if name.lower().endswith('.zip')]
                if nested_zips:
                    threats.append({
                        "type": "zip_nested",
                        "severity": "medium",
                        "message": f"ZIP contains nested ZIP files: {nested_zips}",
                        "matches_count": len(nested_zips)
                    })
        
        except Exception as e:
            logger.error(f"Error scanning ZIP security: {e}")
        
        return threats

# Import io module for BytesIO
import io
