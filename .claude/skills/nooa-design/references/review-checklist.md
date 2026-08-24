# Review Checklist

Audit procedure for an existing agent codebase. Produce findings, not a rewrite.

**Prioritization rule**: rank violations by impact ÷ change cost. Sections 3 (pass by reference) and 2 (typed I/O) usually win — highest token savings, smallest blast radius. Section 9 (safety) preempts everything when it fails.

---

## §1 Structure

- Can one agent's full definition be read in one Python file plus one prompt file?
- Are there hand-written JSON schemas describing things that already have type annotations?
- How many files does one business-rule change touch? Target: 1.
- Is there a workflow graph, callback module, or state module that the class could absorb?

Red flags: `tools.json`, `callbacks.py`, `graph.py`, `state.py` as separate concerns.

---

## §2 Typed I/O

- Does every model-facing method declare a concrete return type — not `str`, `dict`, or `Any`?
- Are returns runtime-validated with auto-retry on violation?
- Is any model output parsed by regex or substring match?
- Does the type checker pass on agent modules?

Red flags: `json.loads(response.text)` inside try/except; `if "yes" in resp.lower()`.

Minimal fix: convert the single most failure-prone method's return type to an Enum or dataclass.

---

## §3 Pass by reference

- Is any file content, query result, or HTML serialized wholesale into a prompt?
- What is the peak prompt-token count per session, as a fraction of the window?
- Is context compaction or summarization in the pipeline? **If yes, treat as a symptom, not a solution** — audit this section before accepting it.
- Is the transcript append-only? What is the prefix cache hit rate?

Red flags: `.to_string()`, `.read()`, `json.dumps(large)` near prompt assembly.

Reference point: upstream SWE-bench sessions peaked at 22–72k against 200–400k windows, needing no compaction. Peaks approaching the window indicate a violation here.

---

## §4 Code as action

- Does tool-call count scale with data row count?
- Can the model write conditionals and loops in a single action?
- Does branching logic live in code, or is it routed through the model?
- Can the model call the agent's own methods via `self`?

---

## §5 Deterministic / agentic boundary

Most commonly violated section. Audit separately.

- Are any business rules stated as prompt instructions rather than enforced by code?
- Can those rules be expressed as if/else, arithmetic, parsing, or state transitions? If yes, they belong in deterministic methods.
- Are critical verification steps enforced by code or requested in prompt text?
- Are there deterministic gates at the decision points that must not fail?

Criterion: if it can be written as if/else, write it as if/else. Reserve `...` for semantic judgment, synthesis, and open-ended tasks.

---

## §6 State and memory

- Does critical state live in typed fields or in the message array?
- What survives a process restart?
- Can state be asserted in tests without mocking the LLM?
- Where does cross-session knowledge live? Is it human-readable and reviewable?
- Is memory curated by the agent, or produced by background summarization?

Red flag: the `messages` array is the only source of truth.

---

## §7 Loop and control

- Is the orchestration loop ordinary code or a framework black box?
- Can retry strategy be changed after the Nth failure by editing code rather than prompt text?
- Where is the termination condition defined?

---

## §8 Observability

- Are LLM calls, code executions, and method invocations all traced?
- Are parent-child spans preserved?
- Can the exact context of a failed run be reconstructed?
- Do spans record the resolved prompt key and registry version?
- Can the model query its own context blocks and event history?

---

## §9 Prompt registry

Project-specific — see `prompt-registry.md`.

- Any prompt text in `.py` files (literals, f-strings, dedent blocks)?
- Does every agentic method declare a prompt key?
- Is the bidirectional CI contract test present and passing?
- Does the contract test check parameter-name parity, not just key existence?
- Is the registry version pinned by the deployment and recorded in traces?
- Is the registry immutable in-process after load?
- Is there a lint rule blocking new inline prompt literals?

Parameter-name parity is the one that fails silently. Its absence is a high-priority finding even when everything else passes.

---

## §10 Safety

- Does the agent execute model-generated code?
- If yes, is it confined to a container, VM, or OpenShell?
- Is network egress denied by default?
- Is the filesystem read-only by default with explicit writable paths?
- Is every run auditable after the fact?

Any failure here outranks every other finding. AST checks and deny-lists are guardrails, not a containment boundary. The boundary is OS-level isolation.

---

## Output format

Produce findings in exactly this structure:

```
## Assessment
Two or three sentences: current shape of the codebase, primary structural problem.

## Findings
§1  Structure          PASS / FAIL — one line
§2  Typed I/O          ...
§3  Pass by reference  ...
§4  Code as action     ...
§5  Det/agentic split  ...
§6  State and memory   ...
§7  Loop and control   ...
§8  Observability      ...
§9  Prompt registry    ...
§10 Safety             ...

## Prioritized remediation
1. [HIGH]   <violation> → <fix> → <expected effect, quantified where possible>
2. [MEDIUM] ...
3. [LOW]    ...

## Leave alone
Violations where change cost exceeds benefit this round. Name them explicitly with the reason.
```

The final section is required. A review that flags everything has not prioritized anything.
