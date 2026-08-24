# Patterns

Before/after code for each capability, plus a full refactor. Prompts are external throughout — see `prompt-registry.md`.

Contents:
1. [Typed I/O](#1-typed-io)
2. [Pass by reference](#2-pass-by-reference)
3. [Code as action](#3-code-as-action)
4. [Programmable loop](#4-programmable-loop)
5. [Explicit state](#5-explicit-state)
6. [Model-callable APIs](#6-model-callable-apis)
7. [Full refactor](#7-full-refactor)
8. [Boundary clarifications](#8-boundary-clarifications)

---

## 1. Typed I/O

### Before

```python
PROMPT = open("prompts/classify.txt").read()

async def classify(message: str) -> str:
    resp = await llm.complete(PROMPT.format(msg=message))
    return resp.text

kind = await classify(msg)
if "refund" in kind.lower():          # caller guesses
    ...
```

`kind` may be `"refund"`, `"Refund request"`, a sentence, or an apology. No failure signal.

### After

```python
class TicketKind(StrEnum):
    REFUND = "refund"
    SHIPPING = "shipping"
    TECHNICAL = "technical"
    OTHER = "other"

class SupportAgent(Agent):
    prompts: PromptSet

    @agentic(prompt="support.classify")
    async def classify(self, message: str) -> TicketKind:
        """Classify an inbound message. Documentation only."""
        ...
```

Gains: runtime validation with auto-retry, `match` instead of substring checks, static type checking, no schema file.

### Composite returns

```python
@dataclass
class Ticket:
    kind: TicketKind
    priority: int
    summary: str
    needs_human: bool

@agentic(prompt="support.triage")
async def triage(self, message: str, order: Order | None) -> Ticket:
    """Build a structured ticket."""
    ...
```

`Ticket` serves as output schema, validation rule, and field documentation. Do not hand-write a parallel JSON schema.

---

## 2. Pass by reference

### Before

```python
def read_logs(path: str) -> str:
    return open(path).read()                     # 80k tokens

messages.append({"role": "tool", "content": read_logs("/var/log/app.log")})
# persists in context for every subsequent turn
```

Three turns in, context overflows; compaction starts; cache invalidates; cost doubles.

### After

```python
class LogAgent(Agent):
    prompts: PromptSet
    log_store: LogStore                          # live object on the agent

    @agentic(prompt="log.root_cause")
    async def find_root_cause(self, incident: str) -> Diagnosis:
        """Identify the root cause of an incident."""
        ...
```

What the model sees in the REPL:

```
log_store  # <LogStore: 412,003 lines, 2026-08-01 → 2026-08-24>
```

What the model writes to get detail:

```python
errs = log_store.filter(level="ERROR", since="2026-08-24T03:00")
errs.top_messages(5)                             # only 5 lines enter context
```

### Conversion table

| Data | By value | By reference |
|---|---|---|
| File | `f.read()` into prompt | `Path` or `Document` object with query methods |
| SQL result | rendered as a markdown table | DataFrame or cursor object |
| Web page | full HTML | `Page` object with `.text()`, `.links()` |
| Previous step output | serialized and re-pasted | left as a REPL variable |

---

## 3. Code as action

### Before — N round trips

```
model  → get_orders(user_id=42)
harness→ [180 orders as JSON]
model  → check_refund_eligible(order_id=1001)
harness→ true
model  → check_refund_eligible(order_id=1002)
...                                              # 178 more LLM calls
```

### After — one action

```python
orders = self.order_db.for_user(42)
eligible = [o for o in orders if self.is_refund_eligible(o)]
total = sum(o.amount for o in eligible)
f"{len(eligible)} eligible, {total} total"
```

`self.is_refund_eligible` is deterministic:

```python
def is_refund_eligible(self, order: Order) -> bool:
    """Refund window check."""
    return order.delivered and order.days_since_delivery <= 30
```

The rule is enforced by code. It is never stated in prompt text.

### Deterministic gates

Upstream's vulnerability-discovery pipeline is one object with three deterministic gate methods: convert verifier output to a crash/no-crash verdict, confirm the crash matches the reported vulnerability, re-run the input to confirm reproduction.

Because the gates are typed methods rather than free text passed between processes, a finding is accepted only when code says so, and the whole run is one inspectable trace. Result: 86.8% on CyberGym L1 with network access blocked.

Apply this shape wherever correctness must be guaranteed rather than encouraged.

---

## 4. Programmable loop

### Before

```python
agent = SomeFramework.create(tools=[...], max_iters=10)
result = agent.run(task)                         # internals opaque
```

Retry strategy can only be influenced through prompt text.

### After

```python
class ResearchAgent(Agent):
    prompts: PromptSet
    max_sources: int = 20

    async def research(self, topic: str) -> Report:
        # developer-written loop, ordinary Python
        findings: list[Finding] = []
        for _ in range(3):
            batch = await self.gather(topic, exclude=findings)
            if self.quality_ok(batch):           # deterministic check
                findings.extend(batch)
                break
            topic = await self.reframe(topic)    # fallback in code, not prompt
        return await self.write_report(findings)

    def quality_ok(self, batch: list[Finding]) -> bool:
        return len(batch) >= 3 and all(f.has_source for f in batch)

    @agentic(prompt="research.gather")
    async def gather(self, topic: str, exclude: list[Finding]) -> list[Finding]:
        """Gather findings on a topic."""
        ...
```

`research` has a real body — deterministic. `gather`, `reframe`, `write_report` are agentic. Mixing both in one class is the point.

---

## 5. Explicit state

### Before

```python
messages = [
    {"role": "system", "content": "Budget is 100."},
    ...
    # turn 40: what is the remaining budget? the model must recompute from history
]
```

History gets truncated or summarized; the budget line may no longer be in context.

### After

```python
class ShoppingAgent(Agent):
    prompts: PromptSet
    budget_remaining: int = 100
    items_in_cart: list[Item] = field(default_factory=list)
    rejected: list[tuple[Item, str]] = field(default_factory=list)

    def can_afford(self, item: Item) -> bool:
        return item.price <= self.budget_remaining
```

Gains: `assert agent.budget_remaining >= 0` in tests without mocking the LLM; serializable for resume; the model reads the current value every turn rather than recalling a statement from 40 turns ago.

### Long-term memory

For cross-session knowledge, use a curated store rather than background summarization:

- Model writes, queries, and corrects records through callable tools
- Relevant records surface spontaneously into context
- Records carry type, importance, tags, and typed relations (`supports`, `contradicts`, `derived-from`) — a graph, not a log
- Background reflection pass merges duplicates, links related records, distills episodes, prunes stale entries
- Single human-readable SQLite file; inspectable, backupable, reviewable; shareable across agents with separate ownership

Upstream measured +11.8 points RHAE on ARC-AGI-3 over file-based notes.

---

## 6. Model-callable APIs

### Before

```python
def build_prompt(task, history, docs):           # external, invisible to the model
    return f"{SYSTEM}\n\n{docs}\n\n{history}\n\n{task}"
```

The model cannot inspect how its context was assembled or what is in it.

### After

Static text comes from the registry; blocks stay model-callable.

```python
class Assistant(Agent):
    prompts: PromptSet

    @agentic(prompt="assistant.handle")
    async def handle(self, task: str) -> str:
        """Handle a task."""
        self.context.blocks["reference"] = self.load_docs(task)   # developer-side
        ...
```

Model-side, still available:

```python
self.context.blocks.keys()          # what is in my context?
self.events.since(step=5)           # what did I do after step 5?
self.context.blocks["scratch"] = "" # clear a block I no longer need
```

Externalizing prompt text does not remove this. If the block API becomes read-only or invisible to the model, capability 6 is broken — fix it.

### Tracing

Every LLM call, code execution, and method invocation traced by default, parent-child spans preserved across orchestrators, agentic methods, and helpers. Include the resolved prompt key and registry version in each span so runs are reproducible.

---

## 7. Full refactor

### Before — fragmented

```
support_bot/
├── prompts/
│   ├── system.txt
│   ├── classify.txt
│   └── respond.txt
├── tools.py            # hand-written JSON schema
├── callbacks.py
├── graph.py            # workflow nodes and edges
└── state.py            # TypedDict
```

Changing one business rule touches three files. Debugging spans five.

### After — one class plus a registry

```yaml
# prompts/support_agent.yaml
version: 1
agent: SupportAgent
system: |
  You are a support agent for a customer service system.
  Be thorough and verify order details before making changes.
methods:
  support.classify:
    template: |
      Classify the customer message into the best ticket kind.
      Message:
      {{ message }}
    params: [message]
  support.triage:
    template: |
      Triage this message and produce a support ticket.
      Message:
      {{ message }}
    params: [message, order]
```

```python
from dataclasses import dataclass, field
from enum import StrEnum

class TicketKind(StrEnum):
    REFUND = "refund"; SHIPPING = "shipping"; TECHNICAL = "technical"; OTHER = "other"

@dataclass
class Ticket:
    kind: TicketKind
    priority: int
    summary: str
    needs_human: bool

class SupportAgent(Agent):
    # injected
    prompts: PromptSet
    order_db: OrderDB

    # typed state
    handled_today: list[Ticket] = field(default_factory=list)
    escalation_budget: int = 5

    # deterministic capabilities
    def is_refund_eligible(self, order: Order) -> bool:
        """Refund window check."""
        return order.delivered and order.days_since_delivery <= 30

    def can_escalate(self) -> bool:
        """Remaining human-escalation quota."""
        return self.escalation_budget > 0

    # agentic capabilities
    @agentic(prompt="support.classify")
    async def classify(self, message: str) -> TicketKind:
        """Classify an inbound message."""
        ...

    @agentic(prompt="support.triage")
    async def triage(self, message: str, order: Order | None) -> Ticket:
        """Build a structured ticket."""
        ...

    # developer-written orchestration
    async def handle(self, message: str, order: Order | None) -> Reply:
        ticket = await self.triage(message, order)
        if ticket.needs_human and self.can_escalate():
            self.escalation_budget -= 1
            return await self.escalate(ticket)
        self.handled_today.append(ticket)
        return await self.reply(ticket)
```

Two artifacts instead of six: one Python file under code review, one YAML file under CD. Both versioned, both diffable, bound by the contract test.

---

## 8. Boundary clarifications

Points that are commonly misread. State them explicitly when they come up.

### `order_db: OrderDB` does not initialize or connect anything

It is a class-level annotation — an entry in `__annotations__`, equivalent to a dataclass field declaration. It declares "this field is model-visible state." Nothing more.

Connection is ordinary Python at the composition root:

```python
engine = create_engine("sqlite:///orders.db")
agent = SupportAgent(prompts=pset, order_db=OrderDB(engine))
```

Connection lifecycle, pooling, and reconnection remain the caller's concern. The framework does not manage them.

### Querying with SQL or pandas is not the same as pass by reference

Two separate concerns:

| Concern | What it is | Capability |
|---|---|---|
| Who fetches the data | model writes `SELECT` or pandas operations | code as action |
| Where the result lives | in a process variable, preview only in context | pass by reference |

**Test: do the full contents of this data become characters in the prompt?** The answer is independent of the query engine.

```python
# used SQL, only 10 rows — still pass by VALUE
rows = db.execute("SELECT * FROM orders LIMIT 10").fetchall()
prompt += str(rows)                    # full contents became prompt characters
```

```python
# 400k rows — pass by REFERENCE
df                                     # model sees: <DataFrame 412003 rows × 8 cols>
```

Worked comparison — "top three refund customers last month":

```python
# by value
rows = conn.execute("SELECT * FROM refunds WHERE month='2026-07'").fetchall()
messages.append({"role": "tool", "content": json.dumps(rows)})
# 12,000 rows ≈ 400k tokens → overflow → compaction → cache invalidated
```

```python
# by reference — model-written, one execution
df = pd.read_sql("SELECT customer_id, amount FROM refunds WHERE month='2026-07'",
                 self.order_db.conn)
top3 = df.groupby("customer_id").amount.sum().nlargest(3)
top3                                   # 3 rows enter context
```

`df` stays live. A follow-up computation reuses it without re-querying or re-serializing. This is why compaction is unnecessary — the bulk never entered context.

### Why `self` matters

The REPL namespace binds `self`, so `self.order_db` resolves to the same object in memory, not a copy. That is Python's native reference semantics, which is where the capability name comes from.

### Prompts are external here — do not reintroduce docstring prompts

Upstream uses docstrings as prompts. This project does not. Docstrings are documentation for humans and IDEs and are never sent to the model. Do not propose reverting, and do not cite docstring co-location as a benefit. The drift protection it would provide is supplied instead by the CI contract test in `prompt-registry.md` §4.

---

## Safety

Any agent that executes model-generated code runs in a sandbox.

AST validation and module deny-lists are defense-in-depth, not a containment boundary. Static analysis cannot contain Python: `open()` gives arbitrary file access, `importlib` loads modules from a path, reflection reaches the rest.

The containment boundary is OS-level isolation — container, VM, or NVIDIA OpenShell. Never rely on in-process validators alone.
