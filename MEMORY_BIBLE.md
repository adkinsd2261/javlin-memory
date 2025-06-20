
# 📝 MEMORY_BIBLE.md

> **Defines memory schemas, logging principles, and data handling standards for all MemoryOS operations.**

---

## 1. Memory Schema Standards

### Core Memory Structure
```json
{
  "topic": "string (required, max 200 chars)",
  "type": "string (required, enum: BugFix|Feature|Decision|Insight|BuildLog|SystemTest|Enhancement|Reflection|Emotion)",
  "input": "string (required, what was attempted/inputted)",
  "output": "string (required, what was the result/output)",
  "score": "integer (required, 0-25, achievement score)",
  "maxScore": "integer (required, usually 25)",
  "success": "boolean (required, was this successful)",
  "category": "string (required, enum: system|development|integration|monitoring|Infrastructure)",
  "tags": "array[string] (optional, max 5 tags)",
  "context": "string (optional, auto-generated summary)",
  "related_to": "array[string] (optional, related memory topics)",
  "reviewed": "boolean (required, default false)",
  "timestamp": "string (required, ISO 8601 format)",
  "auto_generated": "boolean (optional, true if ML/auto-generated)"
}
```

---

## 2. Memory Types and Usage

- **BugFix**: Problem resolution, error fixes, debugging outcomes
- **Feature**: New functionality implementation, feature additions
- **Decision**: Strategic choices, architectural decisions, trade-offs
- **Insight**: Learning moments, discoveries, breakthrough understanding
- **BuildLog**: System builds, deployments, infrastructure changes
- **SystemTest**: Testing outcomes, validation results, QA activities
- **Enhancement**: Improvements to existing functionality
- **Reflection**: Process analysis, retrospectives, optimization thoughts
- **Emotion**: Frustration, satisfaction, breakthrough moments

---

## 3. Auto-Logging Rules

- Importance score ≥60 required for auto-logging (≥40 for trusted agents)
- All auto-generated entries marked with `auto_generated: true`
- ML predictions preferred when confidence >0.6, fallback to heuristics
- Trusted agents (Javlin Builder Agent, Assistant) have lower thresholds

---

## 4. Data Retention and Privacy

- Memories retained for 90 days unless marked for long-term storage
- No PII or secrets logged unless explicitly documented
- Export available via `/memory` endpoint in JSON format
- Deletion requests processed within 24 hours

---

## 5. Quality Standards

- All entries must have meaningful `topic` (not generic)
- `input` and `output` should be specific and actionable
- Success/failure must be accurately marked
- Context auto-generated when missing but encouraged manual addition

---

## 6. Changelog

- **2025-06-20 — Initial version aligned with current memory.json schema**
- [add more as schema evolves]

---

**All memory operations must comply with this MEMORY_BIBLE. Reference this in every memory-related function.**
