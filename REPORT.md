# 1. Architecture

The system is designed as a small end-to-end vertical slice that separates LLM-driven discovery from deterministic production replay.

The main flow is:

```text
Natural-language goal
        ↓
LLM discovery loop
        ↓
Live UI interaction through Playwright
        ↓
Successful run recorded as structured history
        ↓
Typed capability artifact generated
        ↓
Deterministic replay without an LLM

# 2. Artifact schema

The capability artifact is the boundary between LLM-driven discovery and deterministic replay. I intentionally keep it separate from the raw model transcript so that the production path does not depend on free-form reasoning text.

Each artifact includes:

- a schema version
- a capability name and description
- the target application and entry point
- typed input parameters
- typed output parameters
- an ordered list of executable steps
- locator information for each target
- a success checkpoint
- known business outcomes
- known hard failures

For the example capability, the contract is:

```text
Capability:
lookup_savings_balance

Input:
member_id: string

Output:
savings_balance: string

# 3. Determinism & error handling

Deterministic replay is the production execution path. Once a discovery run succeeds and a capability artifact is generated, replay executes the recorded steps directly without asking an LLM what to do.

The replay engine:

1. loads the saved capability artifact,
2. substitutes invocation-time inputs such as `member_id`,
3. resolves each recorded target,
4. executes the steps in order,
5. extracts declared outputs,
6. checks for known runtime conditions,
7. verifies the final checkpoint,
8. returns a structured result.

A successful replay for the example capability returns:

```json
{
  "status": "success",
  "outputs": {
    "savings_balance": "$4,821.77"
  },
  "llm_calls": 0
}

# 4. Heterogeneity & multi-tenant

The implementation targets one browser-based demo application, but the core abstractions are designed so the recorded capability is not tightly coupled to Playwright or to one tenant-specific DOM.

The main seam is the `ComputerSurface` abstraction.

The current implementation provides:

```text
PlaywrightSurface

# 5. Escalation & handoff

The system treats human intervention as an explicit control-state transition rather than as an out-of-band manual workaround.

The handoff controller models these states:

```text
AUTOMATION
→ PAUSED
→ HUMAN
→ RESUMING
→ AUTOMATION

# 6. Safety

The safety model is intentionally explicit and conservative because the target environment represents regulated financial workflows.

The system enforces a configurable policy over:

```text
allowed hosts
allowed routes
allowed actions
risky actions
blocked actions

# 7. Cuts

I intentionally kept the implementation focused on one complete vertical slice rather than adding broad infrastructure that was not required to demonstrate the core design.

The current implementation does not include:

```text
a production operator console
desktop automation
distributed workers or queues
multi-tenant deployment infrastructure
artifact approval workflows
automatic capability version migration
cross-tenant override management
long-term replay stability scoring
bounded LLM recovery during replay