
# 🕵️ PRIVACY_POLICY.md

> **Explains user data rights, memory handling, and compliance for all users of MemoryOS/Javlin.**

---

## 1. Data We Collect

### Memory Logs
- **Structured text entries**: Topics, inputs, outputs, categories
- **System metadata**: Timestamps, success flags, importance scores
- **Auto-generated context**: Tags, relationships, ML predictions
- **User feedback**: Ratings and comments on memory entries

### Session Information
- **Agent decisions**: Auto-logging choices and reasoning
- **System health data**: API usage, performance metrics
- **Git integration**: Commit messages, file changes (no file contents)

### What We DON'T Collect
- **No secrets or passwords** unless explicitly entered by user
- **No personal identification** unless provided voluntarily
- **No file contents** - only metadata and user-provided summaries
- **No keystroke logging** or screen recording

---

## 2. User Rights

### Data Access
- Export all your memories via `GET /memory` endpoint
- View complete data in JSON format for full transparency
- Access system health information affecting your data

### Data Control
- **Delete individual memories** via API request
- **Bulk data deletion** available on request
- **Opt out of auto-logging** via system configuration
- **Control data retention periods** (default: 90 days)

### Data Portability
- All exports in standard JSON format
- No vendor lock-in - data is yours
- Migration tools available for common formats

---

## 3. Data Usage

### Primary Use
- **Memory system functionality**: Storing and retrieving your logged experiences
- **Auto-logging optimization**: ML training to improve relevance
- **System insights**: Pattern recognition for better user experience

### Secondary Use
- **System health monitoring**: Aggregate usage statistics (anonymized)
- **Product improvement**: Understanding feature usage patterns
- **Security monitoring**: Detecting unusual access patterns

### What We Don't Do
- **Never sell your data** to third parties
- **No advertising** or marketing use of personal data
- **No behavioral tracking** beyond system functionality
- **No cross-user data sharing** without explicit consent

---

## 4. Data Storage and Security

### Storage Location
- Data stored securely in Replit environment
- **No third-party storage** for sensitive memory data
- Backups encrypted and access-controlled

### Security Measures
- API authentication required for write operations
- Input validation and sanitization
- Regular security audits (see SECURITY_BIBLE.md)
- Access logging for all data operations

### Data Retention
- **Default retention**: 90 days for auto-generated memories
- **User-marked important**: Retained until user deletion
- **System logs**: 30 days for security and debugging
- **Automatic cleanup**: Old data pruned according to policy

---

## 5. Sharing and Disclosure

### When We Share Data
- **Never** - unless legally required or with explicit user consent
- **Legal compliance**: Only when required by law with proper documentation
- **Security incidents**: Only affected users notified with details

### Third-Party Integrations
- **Git hosting**: Only metadata shared (commit messages, not code)
- **ML services**: Data anonymized if used for model training
- **Analytics**: Only aggregate, non-personal statistics

---

## 6. International Users

### Data Processing
- Data processed in accordance with user's local privacy laws
- **EU users**: GDPR rights fully supported
- **California users**: CCPA compliance maintained
- **Other jurisdictions**: Best practice standards applied

---

## 7. Changes to Privacy Policy

### Notification
- Users notified of material changes via system health endpoint
- **30 days notice** for significant policy changes
- Continued use constitutes acceptance of changes

### Version Control
- All policy versions maintained in changelog
- Previous versions available for reference

---

## 8. Contact and Complaints

### Data Requests
- Email privacy requests to system owner
- Response within **7 business days** for most requests
- Deletion requests processed within **24 hours**

### Complaints
- Privacy concerns logged as BugFix in memory system
- External privacy authorities available for unresolved issues

---

## 9. Compliance Certifications

- **GDPR-ready**: All required capabilities implemented
- **CCPA-compliant**: California privacy rights supported
- **SOC 2 principles**: Security and availability controls
- **Regular audits**: Compliance verified through infrastructure audit

---

## 10. Changelog

- **2025-06-20 — Initial privacy policy draft**
- [add more as policy evolves]

---

**This privacy policy is legally binding. All data handling must comply with these terms.**
