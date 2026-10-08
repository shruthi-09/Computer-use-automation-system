# Computer-Use Automation System

A focused end-to-end implementation of an LLM-driven computer-use automation system.

The system demonstrates how an LLM can discover how to complete a task in a live UI, convert the successful run into a structured reusable capability, and replay that capability deterministically with no LLM in the decision loop.

The demo uses a synthetic credit-union member-service application as a safe stand-in for a legacy banking back-office system.

## What It Demonstrates

The project includes:

- real LLM-driven UI discovery
- Playwright browser automation
- structured and versioned capability artifacts
- deterministic replay with `llm_calls = 0`
- typed inputs and outputs
- business-outcome handling
- hard-failure handling
- configurable safety guardrails
- sensitive-data redaction
- human-in-the-loop pause / takeover / resume
- structured discovery and replay evidence
- screenshot evidence for failures and handoff

The core lifecycle is:

```text
Natural-language goal
        ↓
LLM observe → decide → act loop
        ↓
Successful discovery history
        ↓
Typed capability artifact
        ↓
Deterministic replay
        ↓
Structured result