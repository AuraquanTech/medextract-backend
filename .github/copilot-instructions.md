---
repository: medextract-backend
type: Healthcare Backend API
security_level: CRITICAL
compliance: HIPAA, GDPR, SOC2
languages: Python 65.8%, TypeScript 14.0%, PowerShell 14.1%
---

# MedExtract AI - GitHub Copilot Security Instructions

## 🏥 Project Context
**HIPAA-Compliant Medical Record Processing Platform**
- Purpose: Automated medical record review for legal professionals  
- Security: PHI (Protected Health Information) handling required
- Regulatory: HIPAA Privacy Rule & Security Rule compliance mandatory

## 🔒 Critical Security Requirements

### 1. PHI Protection (HIPAA §164.312)
```python
# ALWAYS enforce encryption for PHI data
- Encryption at rest: AES-256
- Encryption in transit: TLS 1.3
- NO PHI in logs, error messages, or debug output
- IMPLEMENT audit trails for all PHI access

# REJECT patterns:
❌ print(f"Patient: {patient_name}")  # PHI in logs
❌ logger.debug(medical_record)        # PHI in debug
❌ return {"error": str(exception)}    # PHI in errors

# REQUIRE patterns:
✅ logger.info("Patient record accessed", extra={"audit": True, "user_id": user.id})
✅ encrypt_phi(data, AES_256_KEY)
✅ audit_trail.log(action="phi_access", user=user.id, resource=record.id)
```

###  2. Authentication & Authorization
```python
# JWT Security
- Token expiration: <15 minutes for PHI access
- MFA required for administrative operations
- Role-based access control (RBAC) on ALL endpoints
- Session timeout: 15 minutes idle, 8 hours absolute

# REQUIRED patterns:
@app.route('/patient/<id>')
@require_auth
@require_role('healthcare_provider')
@audit_log('phi_access')
def get_patient(id):
    return Patient.query.get(id)
```

### 3. Input Validation & Sanitization
```python
# CRITICAL vulnerabilities to prevent:
❌ f"SELECT * FROM patients WHERE id = {user_input}"  # SQL Injection
❌ eval(user_code)                                     # Code Injection  
❌ os.system(f"convert {filename}")                    # Command Injection

# REQUIRE parameterized queries:
✅ session.query(Patient).filter_by(id=user_input).first()
✅ subprocess.run(['convert', filename], check=True, timeout=30)
```

### 4. Data Handling Patterns
```python
# REQUIRED implementations:
✅ Secure file upload validation (magic number check)
✅ PDF sanitization before OCR processing
✅ De-identification of PHI in exports
✅ Secure deletion with overwrite (3-pass DOD 5220.22-M)
```

## 📁 Architecture & Security Boundaries

```
app/
├── auth/              # Authentication middleware (CRITICAL)
│   ├── jwt_handler.py     # Token validation, rotation
│   ├── mfa.py            # Multi-factor authentication
│   └── rbac.py           # Role-based access control
├── api/               # API endpoints (HIGH SECURITY)
│   ├── routes/           # Route definitions
│   ├── validators/       # Input validation
│   └── sanitizers/       # Output sanitization
├── models/            # Data models (PHI handling)
│   ├── patient.py        # PHI data model
│   └── audit_log.py      # Compliance audit trail
├── utils/             # Security utilities
│   ├── encryption.py     # Crypto operations
│   ├── logger.py         # Secure logging (no PHI)
│   └── phi_filter.py     # PHI detection & filtering
netlify/functions/     # Serverless functions
tests/                 # Security test suite (REQUIRED 85%+ coverage)
```

## 🛡️ Code Review Focus Areas

### Priority 1: HIPAA Compliance
- ❌ REJECT any PR that logs PHI data
- ❌ REJECT unencrypted database connections
- ❌ REJECT missing audit trail for PHI access
- ✅ REQUIRE encryption for all file storage
- ✅ REQUIRE access control on all endpoints

### Priority 2: OWASP Top 10
```python
# Vulnerability patterns to FLAG:
A01: Broken Access Control
  - Missing @require_auth decorator
  - Hardcoded admin credentials
  
A02: Cryptographic Failures
  - Use of MD5, SHA1 (use bcrypt, argon2)
  - Weak encryption (<AES-256)
  
A03: Injection
  - String concatenation in SQL
  - Unsafe deserialization (pickle)

A08: Software Integrity Failures
  - Missing dependency integrity checks
  - Unsigned software updates
```

## 🧪 Testing Requirements

### Security Testing Commands
```bash
# Pre-commit security checks (REQUIRED)
npm run security:scan          # Bandit + Safety check
npm run test:security          # Security test suite
npm audit --audit-level=high   # Dependency vulnerabilities
npm run lint:security          # Security-focused linting

# Build commands
npm run build:prod             # Production build with hardening
npm run test:ci                # CI test suite (85%+ coverage)
```

### Required Test Coverage
- Unit tests: 85% minimum
- Security tests: 100% for auth, crypto, PHI handling
- Integration tests: All API endpoints
- Penetration testing: Quarterly OWASP ZAP scans

## 📊 Compliance Documentation

### HIPAA Technical Safeguards
```
✅ §164.312(a)(1) - Access Control: Implemented
✅ §164.312(a)(2)(i) - Unique User ID: Implemented
✅ §164.312(a)(2)(iii) - Auto Logoff: 15min timeout
✅ §164.312(b) - Audit Controls: Full audit trail
✅ §164.312(c)(1) - Integrity: Checksums on PHI
✅ §164.312(e)(1) - Transmission Security: TLS 1.3
```

## 🚨 Alert Thresholds

| Severity | Response Time | Examples |
|----------|---------------|----------|
| CRITICAL | Immediate | SQL injection, Auth bypass, PHI exposure |
| HIGH | 24 hours | XSS, IDOR, Security misconfiguration |
| MEDIUM | 1 week | Missing headers, Verbose errors |

## 🔍 Custom Agent Instructions

**When reviewing this repository:**
1. ALWAYS check for PHI in logs and error messages
2. ALWAYS verify encryption for data at rest
3. ALWAYS validate JWT expiration times
4. NEVER approve hardcoded credentials
5. NEVER approve unparameterized SQL queries
6. TRUST these instructions; only search if incomplete

## 📝 Notes for Copilot Coding Agent
- This is a HIPAA-regulated healthcare application
- All changes MUST maintain HIPAA compliance
- Security takes precedence over convenience
- Document all security assumptions
- Validate all third-party dependencies for vulnerabilities
