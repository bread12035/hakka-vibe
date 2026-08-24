---
name: nooa-design
description: Apply NVIDIA NOOA (Object-Oriented Agents) architecture to agent code — one agent is one class, methods are capabilities, fields are typed state, type annotations are runtime-enforced contracts, and prompts are loaded from an external registry (not docstrings). Enforces six harness capabilities — typed I/O, pass by reference, code as action, programmable loop, explicit object state, model-callable APIs. Use this whenever writing, reviewing, refactoring, or designing anything agent-related — agent classes, tool definitions, LLM call sites, prompt assembly, context management, orchestration loops, multi-agent systems, agent memory or state — or when the user reports token cost, context overflow, compaction, prompt drift, unparseable model output, or untraceable agent behavior. Trigger without the user naming NOOA or "harness".
---

# NOOA Design

Architecture rules for agent code. Apply by default to every agent-related task in this project.

## Quick reference

| Concept | Implementation | Rule |
|---|---|---|
| Agent | one Python class | One agent, one class, one file |
| Capability | method | Deterministic body OR `...` body, never a mix of concerns |
| State | typed field on the class | Never the message array |
| Contract | type annotation | Runtime-validated, auto-retry on violation |
| Prompt | **external registry, injected** | See `references/prompt-registry.md` |
| Docstring | human/IDE documentation only | **Never sent to the model** |
| Tool schema | derived from type signature | Never hand-written JSON |

## Project deviation from upstream NOOA

Upstream NOOA uses class and method docstrings as prompts. **This project does not.**

Prompts are authored in YAML, versioned, delivered by CD, and assembled by a prompt builder at runtime. Methods reference prompts by stable key. Docstrings remain plain documentation and must never reach the model.

This preserves all six capabilities — they concern the model-facing *interface*, not prompt storage. It costs the drift protection that co-located prompts give for free. Replace it with the CI contract test in `references/prompt-registry.md` §4. Do not skip that test; without it, prompt keys and method signatures silently diverge.

Do not propose moving prompts into docstrings. Do not cite docstring-as-prompt as a benefit.

---

## Core shape

```python
class SupportAgent(Agent):
    # ── injected dependencies ──
    prompts: PromptSet            # from external registry, see references/prompt-registry.md
    order_db: OrderDB             # live object, model-visible, passed by reference

    # ── explicit typed state ──
    handled: list[Ticket] = field(default_factory=list)
    escalation_budget: int = 5

    # ── deterministic capability: business rules enforced by code ──
    def is_refund_eligible(self, order: Order) -> bool:
        """Refund window check. Human-facing doc only."""
        return order.delivered and order.days_since_delivery <= 30

    # ── agentic capability: LLM-driven, prompt from registry ──
    @agentic(prompt="support.classify")
    async def classify(self, message: str) -> TicketKind:
        """Human-facing doc only. Prompt lives in prompts/support.yaml."""
        ...

    # ── developer-written orchestration: ordinary Python ──
    async def handle(self, message: str, order: Order | None) -> Reply:
        ticket = await self.triage(message, order)
        if ticket.needs_human and self.escalation_budget > 0:
            self.escalation_budget -= 1
            return await self.escalate(ticket)
        self.handled.append(ticket)
        return await self.reply(ticket)
```

Absent by design: tool registry, hand-written JSON schema, workflow graph, callback file, prompt string literals in code.

---

## The six capabilities

Check every one when designing or reviewing. Each has a detection rule and a fix.

### 1. Typed input/output

Agentic calls take typed arguments and return runtime-validated values.

- **Detect**: return type is `str`, `dict`, `Any`, or missing. Caller uses regex, substring match, or `json.loads` in a try/except.
- **Fix**: return `Enum`, `dataclass`, or Pydantic model. Let the runtime validate and auto-retry.
- **Why**: free text has no failure signal. A typed contract fails loudly and recovers automatically.

### 2. Pass by reference

The model operates on live objects and sees bounded previews. Full values stay in the execution environment.

- **Detect**: `.read()`, `.to_string()`, `json.dumps(large)`, or `str(rows)` anywhere near prompt assembly. Context compaction or summarization in the pipeline. Peak prompt tokens approaching the window.
- **Fix**: pass the object. Expose query methods on it. Let the model write code to extract what it needs.
- **Test**: does the full content of this data become characters in the prompt? If yes, it is by value regardless of how you queried it.
- **Why**: upstream benchmark — 82.2% on SWE-bench Verified at 29 calls / ~1.1M tokens, against 78.2% at 66 calls / 2.2M for comparison harnesses. Session peaks stayed at 22–72k against 200–400k windows, so no compaction was needed and prefix cache hits compounded.

### 3. Code as action

The model acts by writing Python with control flow and calls to `self`, not by emitting tool-call JSON.

- **Detect**: tool call count scales with row count. Multi-step flows where each step is a separate LLM round trip. Branch decisions routed through the model.
- **Fix**: expose methods on `self`; let the model compose them in one code block.
- **Why**: one action replaces N round trips, and branching logic stays in code.

### 4. Programmable loop engineering

Orchestration loops are ordinary Python, editable by developers and writable by the model.

- **Detect**: retry, fallback, or termination logic that can only be influenced through prompt text. Framework `.run()` with opaque internals.
- **Fix**: write the loop as a normal method body. Mix deterministic checks with `...` methods freely.

### 5. Explicit object state

Durable typed state lives on the agent object.

- **Detect**: important values recoverable only by reading conversation history. State lost across process restart. Tests that require mocking the LLM to assert on state.
- **Fix**: promote to a typed field. Assert on it directly in tests.
- **Boundary**: conversation history holds *what is being discussed*; fields hold *what the agent knows*.

### 6. Model-callable harness APIs

Context blocks and event history are APIs the model can inspect and manage.

- **Detect**: prompt assembled by an external function the model cannot see or query. No way for the model to ask what is in its context or what it did at step N.
- **Fix**: expose context blocks and event history as callable APIs. In this project the prompt builder is the developer-side half; see `references/prompt-registry.md` §3 for keeping the model-side half intact.

### Long-term memory (when the agent spans sessions)

Curated, not auto-summarized. The model deliberately writes, queries, and corrects records through callable tools; relevant records surface spontaneously into context. Records carry type, importance, tags, and typed relations (`supports`, `contradicts`, `derived-from`) forming a graph rather than a log. A background reflection pass merges duplicates, links related records, distills episodes, and prunes stale entries. Store is a single human-readable SQLite file — inspectable, backupable, reviewable. Upstream measured +11.8 points RHAE on ARC-AGI-3 over file-based notes.

---

## Implementation order

1. **Write the class skeleton.** Method signatures and typed fields first. No prompt work yet.
2. **Split deterministic vs agentic.** Anything expressible as if/else, arithmetic, parsing, or a state transition gets a real body. `...` is only for semantic judgment, synthesis, and open-ended tasks. This is the most commonly violated rule — never encode a business rule as a prompt instruction.
3. **Type every model-facing boundary.** Concrete input types; `Enum`/dataclass/Pydantic outputs. Never `str` or `dict`.
4. **Register prompt keys.** Add entries to the YAML source, wire `@agentic(prompt=...)`, add the contract test. See `references/prompt-registry.md`.
5. **Audit data flow for pass by reference.** Anything that would serialize wholesale into the prompt becomes an object with query methods.
6. **Move state out of conversation into fields.**
7. **Verify tracing.** Every LLM call, code execution, and method invocation traced, with parent-child spans preserved.
8. **Set the sandbox boundary.** See Safety below. Not optional.

---

## Anti-patterns

| Anti-pattern | Replace with |
|---|---|
| Prompt string literals inline in Python | Registry key + injected `PromptSet` |
| Prompt assembled by `f"..."` at the call site | Prompt builder consuming typed params |
| Hand-written JSON schema for tools | Type annotations |
| Tool returns string, caller parses it | Typed return + runtime validation |
| Whole file / query result / HTML into the prompt | Pass by reference, bounded preview |
| Context compaction or summarization pass | Fix pass by reference first — compaction is a symptom |
| N tool calls to walk N rows | One code block |
| Business rule stated in prompt text | Deterministic method |
| Critical state held in message history | Typed field |
| Six specialist agents coordinating | Try one agent plus a skill first |
| AST checks as the security boundary | OS-level sandbox |

On the last row of the coordination point: upstream collapsed the six-agent DreamTeam world-model architecture into one agent plus a 45-line skill and reached 85.1% mean RHAE on ARC-AGI-3 at under $20/game.

---

## Safety

Non-negotiable when the agent executes model-generated code.

AST validation and module deny-lists are defense-in-depth guardrails, **not a containment boundary**. Static analysis cannot contain Python: `open()` gives arbitrary file access, `importlib` loads modules from a path, reflection reaches the rest.

**The containment boundary is OS-level isolation.** Container, VM, or NVIDIA OpenShell. Never rely on in-process validators alone.

Defaults:
- Sandbox from the first commit, not at deployment time
- Network egress denied by default; allowlist per domain
- Filesystem read-only by default; explicit writable paths only
- Every run auditable — full trace plus readable memory store

---

## References

Read the relevant file before producing code:

- `references/prompt-registry.md` — external prompt management: YAML schema, builder contract, injection, CI drift test, migration from inline prompts. **Read before touching any prompt or LLM call site.**
- `references/patterns.md` — before/after code for each capability, plus a full worked refactor from a fragmented project to a single class.
- `references/review-checklist.md` — audit procedure for an existing codebase, with a fixed output format.

Upstream sources:
- Blog: `developer.nvidia.com/blog/six-agent-harness-capabilities-for-higher-model-performance/`
- Code: `github.com/NVIDIA-NeMo/labs-OO-Agents` (Apache 2.0)
- Paper: arXiv 2607.20709

## Constraints on how to apply this

- **Principles, not the package.** The `nooa` library is not required. Judge by whether the six capabilities hold, not by imports.
- **Incremental on existing code.** Do not propose a full rewrite. Identify the highest-value violations — usually typed I/O and pass by reference — and fix those. State explicitly what is not worth changing.
- **Attribute benchmark numbers.** All figures above are vendor-published (NVIDIA). Cite them as such; do not present them as guaranteed outcomes for this project.
- **Upstream is a research preview.** Treat conflicting local constraints as legitimate, not as violations to correct.
