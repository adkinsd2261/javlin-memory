# MemoryOS

A Flask-based persistent AI memory system with intelligent logging, context awareness, and automated insights for development workflows.

**🎯 Project Governance**: This project is governed by comprehensive documentation "bibles" that define all behaviors, boundaries, and standards. Every component must comply with these foundational documents.

## 📖 Core Documentation (Required Reading)

### System Bibles
- **[AGENT_BIBLE.md](./AGENT_BIBLE.md)** - Agent behavior, boundaries, and pipeline integration rules
- **[MEMORY_BIBLE.md](./MEMORY_BIBLE.md)** - Memory schemas, logging standards, and data handling
- **[PRODUCT_BIBLE.md](./PRODUCT_BIBLE.md)** - Product vision, feature boundaries, and user experience
- **[SECURITY_BIBLE.md](./SECURITY_BIBLE.md)** - Security principles, access control, and vulnerability handling

### User & Developer Guides  
- **[API_REFERENCE.md](./API_REFERENCE.md)** - Complete API documentation and schemas
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Contributor guidelines and development standards
- **[PRIVACY_POLICY.md](./PRIVACY_POLICY.md)** - User data rights, retention, and compliance

### Project History
- **[CHANGELOG.md](./CHANGELOG.md)** - Version history and feature evolution
- **[SYSTEM_UPGRADES.md](./SYSTEM_UPGRADES.md)** - Technical enhancements and architecture changes

## 🚀 Quick Start

### 1. System Health Check
```bash
GET /system-health
```
Verify all bible compliance and system status.

### 2. Complete Onboarding  
```bash
GET /onboarding
```
Essential reading - explains capabilities, boundaries, and required manual steps.

### 3. Explore the API
```bash
GET /memory          # View existing memories
GET /stats           # System analytics  
GET /digest          # Weekly insights
POST /memory         # Log new memory (API key + confirmation required)
GET /compliance/audit # Check bible compliance
POST /session/save   # Save current context
GET /session/load/<id> # Restore session context
```

### 4. Set Up Authentication
- Add `JAVLIN_API_KEY` to Replit Secrets
- Use header: `X-API-KEY: your_key` for POST operations

## 🏗️ Architecture Overview

### Core Components
- **Memory System**: Intelligent logging with ML-powered auto-classification
- **Context Engine**: Maintains state awareness for AI agents and development workflows
- **Insight Generator**: Analyzes patterns and provides actionable recommendations  
- **Git Integration**: Automated sync with version control and changelog generation
- **Health Monitor**: Infrastructure audit and compliance verification

### Key Features
- 📝 **Structured Memory Logging** with auto-tagging and relationship mapping
- 🤖 **AI Agent Integration** with clear boundaries and manual confirmation requirements
- 📊 **Analytics Dashboard** via digest endpoint with weekly summaries
- 🔄 **Auto-Logging** with ML predictions and importance scoring
- 🛡️ **Security-First Design** with comprehensive audit trails
- 🔗 **Git Workflow Integration** with automated commit analysis

## 🤖 Agent Compliance Framework

All AI interactions governed by bible documentation:

### ✅ What Agents CAN Do
- Log structured memories via authenticated API with bible compliance validation
- Provide context-aware insights and recommendations  
- Generate automated summaries and analytics
- Monitor system health and comprehensive bible compliance status
- Suggest optimizations based on memory patterns
- Save and restore session context for continuity
- Validate Replit connection status in real-time

### ❌ What Agents CANNOT Do  
- Execute commands without human/Replit Assistant trigger
- Claim features are "live" without endpoint validation AND manual confirmation
- Modify system configurations or security settings
- Access user data without proper authentication
- Bypass manual confirmation requirements per AGENT_BIBLE.md
- Make "live" claims without Replit connection confirmation
- Operate outside bible compliance boundaries

### 🔒 Compliance Requirements
- **Manual confirmation required** for deployment claims
- **Explicit boundaries** documented between automated/manual operations
- **Transparent reporting** of incomplete states and next steps  
- **API-first design** with clear human intervention points
- **Audit trails** for all agent decisions and actions

## 🛠️ Installation & Setup

### Replit Deployment (Recommended)
1. **Fork this Repl** to your account
2. **Set API Key**: Add `JAVLIN_API_KEY` to Replit Secrets  
3. **Run System**: Click "Run" button to start Flask API
4. **Verify Health**: Test `GET /system-health` endpoint

### Environment Variables
```bash
JAVLIN_API_KEY=your_secure_api_key_here
```

### Dependencies
All dependencies managed automatically by Replit via `pyproject.toml`.

## 📊 Usage Examples

### Basic Memory Logging
```python
import requests

# Log a development decision
response = requests.post('https://your-repl.username.repl.co/memory', 
    headers={'X-API-KEY': 'your_key'},
    json={
        'topic': 'API Design Decision',
        'type': 'Decision', 
        'input': 'Choosing between REST and GraphQL',
        'output': 'Selected REST for simplicity and tooling',
        'score': 20,
        'maxScore': 25,
        'success': True,
        'category': 'development',
        'reviewed': False
    })
```

### Analytics and Insights
```python
# Get weekly digest
digest = requests.get('https://your-repl.username.repl.co/digest').json()

# View system statistics  
stats = requests.get('https://your-repl.username.repl.co/stats').json()

# Check unreviewed memories
unreviewed = requests.get('https://your-repl.username.repl.co/unreviewed').json()
```

### Auto-Logging Integration
```python
# Passive auto-logging (no auth required)
requests.post('https://your-repl.username.repl.co/autolog',
    json={
        'input': 'Refactored user authentication',
        'output': 'Improved security and reduced code complexity',
        'topic': 'Auth Refactor'
    })
```

## 🔧 Development Workflow

### 1. Before Making Changes
- Read relevant bible documentation
- Check system health: `GET /system-health`
- Review current memory context: `GET /context`

### 2. During Development  
- Log important decisions and insights
- Use auto-logging for routine operations
- Monitor system health continuously

### 3. After Changes
- Verify bible compliance with test script
- Update relevant documentation
- Log deployment and results
- Run infrastructure audit: `GET /audit`

## 🚨 Important Notes

### Security
- **Never commit API keys** - use Replit Secrets only
- **All bible documentation is legally binding**
- **Report security issues immediately** via memory system

### Compliance
- **AGENT_BIBLE.md compliance required** for all AI interactions
- **Manual confirmation needed** for any "live" feature claims  
- **Data handling must follow PRIVACY_POLICY.md**

### Support
- **System issues**: Log as BugFix in memory system
- **Feature requests**: Check PRODUCT_BIBLE.md alignment first
- **Security concerns**: Follow SECURITY_BIBLE.md reporting procedures

---

## 🔒 Bible Compliance & Governance

All operations are governed by comprehensive bible documentation:

- **AGENT_BIBLE.md** - Agent behavior boundaries and compliance rules
- **MEMORY_BIBLE.md** - Memory schemas and logging standards  
- **PRODUCT_BIBLE.md** - Product vision and feature boundaries
- **SECURITY_BIBLE.md** - Security principles and practices
- **PRIVACY_POLICY.md** - Data rights and compliance
- **CONTRIBUTING.md** - Development standards and bible compliance
- **API_REFERENCE.md** - Complete API documentation

### 🛡️ Universal Compliance and Output Enforcement

MemoryOS features a comprehensive universal compliance layer that:

- **Centralizes ALL output validation** through single compliance middleware
- **Routes every output channel** (API, UI, logs, chat, email) through compliance checks
- **Blocks action language** without verified backend confirmation
- **Enforces AGENT_BIBLE.md** compliance across all interfaces
- **Provides static code analysis** to detect compliance bypasses
- **Audits all outputs** with comprehensive logging and drift detection
- **Prevents human bypasses** with automated detection and alerts

#### Compliance Architecture

```python
# All outputs must use centralized functions
from compliance_middleware import send_user_output, OutputChannel

# Correct usage - routed through compliance
response = send_user_output("System status updated", OutputChannel.API_RESPONSE)

# Or use decorators for functions
@api_output
def my_api_endpoint():
    return "Information provided"  # Automatically validated

# Direct outputs are detected and blocked
return jsonify({"status": "I completed the task"})  # ❌ FLAGGED
```

#### Compliance Validation Levels

- **STRICT**: API responses, UI messages - blocks action language without confirmation
- **MODERATE**: Log messages, notifications - warns but doesn't block
- **PERMISSIVE**: Error messages - logs for audit but allows through

#### Static Analysis & Code Review

```bash
# Run compliance linter
python compliance_linter.py --directory . --fail-on-violations

# Check compliance stats
curl localhost:5000/compliance/stats

# View audit log
curl localhost:5000/compliance/audit
```

#### Compliance Testing

```bash
# Run comprehensive E2E compliance tests
python compliance_tests.py
```

No output bypasses the compliance contract - all channels are validated, audited, and enforced per AGENT_BIBLE.md.

**MemoryOS is production-ready, audit-compliant, and designed for serious development workflows. All operations are governed by comprehensive documentation standards.**