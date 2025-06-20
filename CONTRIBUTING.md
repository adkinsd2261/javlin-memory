# 🤝 CONTRIBUTING.md

> **Guidelines for contributing to Javlin/MemoryOS. All contributors must follow system bibles and project rules.**

---

## 1. Before You Start

### Required Reading
- **[AGENT_BIBLE.md](./AGENT_BIBLE.md)** - Agent behavior and boundaries
- **[MEMORY_BIBLE.md](./MEMORY_BIBLE.md)** - Memory schemas and standards
- **[PRODUCT_BIBLE.md](./PRODUCT_BIBLE.md)** - Product vision and feature boundaries
- **[SECURITY_BIBLE.md](./SECURITY_BIBLE.md)** - Security requirements and practices

### Prerequisites
- Python 3.8+ and familiarity with Flask
- Understanding of REST APIs and JSON schemas
- Git knowledge (basic branching and PR workflow)
- Read through existing codebase structure

---

## 2. Development Environment

### Setup
1. Fork the repository and create feature branch
2. Install dependencies: `pip install -r requirements.txt` (handled by Replit)
3. Set up environment variables in Replit Secrets
4. Run system health check: `GET /system-health`

### Local Testing
- Use Replit's built-in testing environment
- Test all API endpoints before submitting PR
- Verify AGENT_BIBLE.md compliance with test script
- Run document watcher to check for file changes

---

## 3. Code Guidelines

### Python Style
- **Clear, self-documenting code** preferred over clever solutions
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Comprehensive error handling with logging

### Commit Messages
Use conventional commit format:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Testing improvements
- `chore:` - Maintenance tasks

### File Organization
- Core logic in `main.py` with proper docstrings
- Route blueprints in `routes/` directory
- Utilities and modules in separate files
- All config in `config.json` or environment variables

---

## 4. Memory System Contributions

### Adding New Memory Types
1. Update `MEMORY_BIBLE.md` with new type definition
2. Add type to validation in `main.py`
3. Update ML training data if using auto-logging
4. Test with various scenarios

### Schema Changes
- **Backward compatibility required** for existing memories
- Migration scripts for breaking changes
- Update API documentation and examples
- Test with large memory datasets

---

## 5. API Development

### New Endpoints
- Follow REST conventions and existing patterns
- Add proper authentication where needed
- Include comprehensive error handling
- Document in `API_REFERENCE.md`

### Security Requirements
- All endpoints must pass security review
- Input validation and sanitization required
- Rate limiting for public endpoints
- Audit logging for sensitive operations

---

## 6. Testing Requirements

### Automated Tests
- Unit tests for core functionality
- Integration tests for API endpoints
- AGENT_BIBLE.md compliance tests
- Security vulnerability scans

### Manual Testing
- Test all affected workflows
- Verify system health after changes
- Check memory logging and retrieval
- Validate auto-logging accuracy

---

## 7. Pull Request Process

### Before Submitting
1. **Run all tests** and ensure they pass
2. **Update documentation** for any API changes
3. **Reference bible compliance** in PR description
4. **Test system health** after your changes

### PR Requirements
- Clear title and description
- Reference to related issues or features
- Link to relevant bible sections affected
- Screenshots for UI changes
- Performance impact assessment

### Review Process
- All PRs require maintainer review
- Bible compliance verification required
- Security review for sensitive changes
- Performance review for optimization PRs

---

## 8. Documentation Standards

### Code Documentation
- Docstrings for all functions and classes
- Inline comments for complex logic
- README updates for new features
- API documentation completeness

### Bible Updates
- Update relevant bible files for policy changes
- Maintain changelog in each bible
- Cross-reference between bibles
- Version compatibility notes

---

## 9. Reporting Issues

### Bug Reports
- **Log as BugFix** in memory.json when possible
- Use GitHub issues for tracking
- Include reproduction steps
- Provide system health output
- Mention security implications if applicable

### Feature Requests
- Check PRODUCT_BIBLE.md for feature alignment
- Discuss in issues before implementing
- Consider backward compatibility
- Evaluate security and privacy impact

---

## 10. Community Guidelines

### Communication
- Be respectful and constructive
- Focus on technical merit
- Reference documentation in discussions
- Help newcomers understand the system

### Recognition
- Contributors acknowledged in CHANGELOG.md
- Major contributors listed in README.md
- Credit given for significant improvements
- Community contributions celebrated

---

## 11. Release Process

### Version Management
- Semantic versioning (MAJOR.MINOR.PATCH)
- Version bumps logged to memory system
- Changelog updated for each release
- Breaking changes clearly documented

### Deployment
- All releases deployed through Replit
- System health verified post-deployment
- Rollback procedures documented
- User notification for breaking changes

---

## 12. Changelog

- **2025-06-20 — Initial contributor guidelines**
- [add more as process evolves]

---

**Contributing to MemoryOS means upholding our standards. Thank you for helping build a better memory system!**