# Computer-Use Automation System

A small end-to-end computer-use automation system that demonstrates how an LLM can discover a workflow in a live UI, record that workflow as a reusable capability, and replay it deterministically without an LLM in the decision loop.

The project uses a local credit-union member-service application as a safe stand-in for a legacy banking back-office system.

## What It Demonstrates

The system supports:

- Natural-language, LLM-driven UI discovery
- Real browser interaction using Playwright
- Structured and versioned capability artifacts
- Deterministic replay with zero LLM calls
- Typed inputs and outputs
- Business-outcome classification
- Hard-failure classification
- Safety allowlists and risky-action controls
- Sensitive-data redaction
- Human-in-the-loop pause, takeover, and resume
- Structured discovery logs and screenshot evidence

The core lifecycle is:

```text
Natural-language goal
        ↓
LLM-driven discovery
        ↓
Recorded capability artifact
        ↓
Deterministic replay
        ↓
Typed result