# 🧠 MemoryOS AGENT_BIBLE.md - Clean Version

> **This document defines the behavior for the minimal, bulletproof MemoryOS system.**

## 1. System Identity

- MemoryOS Clean is a minimal, bulletproof memory system
- Zero complexity cruft - only essential features
- API-first architecture with health monitoring

## 2. Core Boundaries

- The system has 6 endpoints: `/`, `/health`, `/memory` (GET/POST), `/stats`, `/gpt-status`
- All Git operations are manual - no automation
- API key required for memory creation (POST /memory)
- All responses are JSON format

## 3. Memory Structure

Required fields for memory entries:
- `topic`: String describing the memory
- `type`: Category of memory (SystemUpdate, Feature, BugFix, etc.)
- `input`: What was attempted or input
- `output`: What was the result or output
- `success`: Boolean indicating success/failure
- `category`: Broad category (system, feature, bug, etc.)

## 4. Operational Rules

- System must be simple and bulletproof
- No complex integrations or dependencies
- Health checks must always work
- Memory file must be valid JSON
- All errors must be logged and returned clearly

## 5. Changelog

- **2025-01-20 — Clean rebuild version created**