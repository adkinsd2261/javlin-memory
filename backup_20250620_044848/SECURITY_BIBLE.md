
# 🔒 SECURITY_BIBLE.md

> **Defines security principles, boundaries, and required practices for all agents, endpoints, and infrastructure in Javlin/MemoryOS.**

---

## 1. Access Control

- **Principle of least privilege** for all endpoints and agent actions
- No default open ports except documented APIs
- All sensitive routes (task queue, memory export, admin) require authentication
- API keys stored in environment variables, never in code
- Rate limiting on public endpoints to prevent abuse

---

## 2. Data Handling

- All logs and memory files stored securely (no public directories)
- **No secrets in plain text** — use env vars or Replit Secrets
- Regular audits of memory.json and config files for accidental data leaks
- PII detection and flagging in memory entries
- Automatic redaction of potential sensitive data

---

## 3. Code and Dependency Security

- All dependencies tracked in pyproject.toml with version pinning
- Regular security audits of dependencies
- **No unvetted code execution** (even from queue/tasks) without human approval
- Input validation on all API endpoints
- SQL injection prevention (though we use JSON files currently)

---

## 4. API Security

- **Authentication required** for POST `/memory` endpoint
- CORS configured for appropriate origins only
- Request size limits to prevent DoS attacks
- Input sanitization for all user-provided data
- Audit logging for all authenticated requests

---

## 5. Infrastructure Security

- Secure file permissions for config and memory files
- No root access required for normal operations
- Environment isolation between dev/prod
- Backup encryption for memory data
- Network security (HTTPS only in production)

---

## 6. Vulnerability Reporting and Mitigation

- **Found a bug?** Log in memory as BugFix type, escalate to owner
- **Critical vulnerabilities** patched within 24 hours
- **Non-critical issues** addressed within 72 hours
- **If user data exposed**, immediate notification and remediation
- Public disclosure only after fix is deployed

---

## 7. Agent Security

- Agents cannot execute system commands without explicit human approval
- All agent actions logged and auditable
- No agent can modify security configurations
- Trusted agent list maintained and reviewed regularly
- Agent capabilities clearly bounded and documented

---

## 8. Compliance Requirements

- GDPR-ready data handling procedures
- CCPA compliance for California users
- Audit trail maintenance for all data operations
- Data retention policies enforced automatically
- User data export/deletion capabilities

---

## 9. Security Monitoring

- Failed authentication attempts logged
- Unusual API usage patterns detected
- System health includes security status
- Regular security assessment as part of infrastructure audit
- Incident response procedures documented

---

## 10. Changelog

- **2025-06-20 — Initial security framework and principles**
- [add more as security measures evolve]

---

**All system components must comply with this SECURITY_BIBLE. Security is not optional - it's foundational.**
