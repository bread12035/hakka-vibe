# Prompt Registry

Prompts are external artifacts: authored in YAML, versioned, delivered by CD, assembled by a builder at runtime, injected into the agent. This file is authoritative for this project and overrides upstream NOOA's docstring-as-prompt convention.

Read this before writing or modifying any LLM call site.

Contents:
1. [Rules](#1-rules)
2. [YAML source format](#2-yaml-source-format)
3. [Builder contract](#3-builder-contract)
4. [CI drift test](#4-ci-drift-test)
5. [Injection and lifecycle](#5-injection-and-lifecycle)
6. [Migrating inline prompts](#6-migrating-inline-prompts)

---

## 1. Rules

| Rule | Reason |
|---|---|
| No prompt text in `.py` files — no literals, no f-strings, no `textwrap.dedent` blocks | Single source of truth; CD owns prompt delivery |
| Docstrings are documentation only, never sent to the model | Removes ambiguity about what the model actually receives |
| Every agentic method declares a prompt key | Makes the method ↔ prompt binding checkable |
| Prompt keys are stable; renaming a key is a breaking change | Keys are the contract surface between code and CD |
| Variable substitution takes typed values, never pre-formatted strings | Preserves typed I/O through the prompt layer |
| Registry is immutable in-process after load | A prompt must not change mid-session; caching and tracing depend on it |
| Version pinned per deployment | Reproducible runs; a trace can be replayed against the exact prompt set |

**What is still typed.** Moving prompts out does not weaken capability 1. The builder receives typed parameters and the method still declares a validated return type. Only the *instruction text* moved; the *contract* stays in Python.

---

## 2. YAML source format

One file per agent. Path mirrors the module path.

```yaml
# prompts/support_agent.yaml
version: 3
agent: SupportAgent

system: |
  You are a support agent for a customer service system.
  Be thorough and verify order details before making changes.

methods:
  support.classify:
    description: Classify an inbound customer message.
    template: |
      Classify the customer message into the best ticket kind.

      Message:
      {{ message }}
    params: [message]

  support.triage:
    description: Build a structured ticket from a message and optional order.
    template: |
      Triage this customer message and produce a support ticket.

      Message:
      {{ message }}
      {% if order %}
      Order: {{ order.id }} — delivered={{ order.delivered }}, days_since={{ order.days_since_delivery }}
      {% endif %}
    params: [message, order]

blocks:
  reference:
    description: Retrieved policy documents, injected at runtime.
  scratch:
    description: Model-managed working notes.
```

Field notes:

- `version` — bumped on any change; pinned by the deployment.
- `system` — the agent-level system prompt. One per agent.
- `methods.<key>.params` — declared parameter names. The CI test asserts these match the Python signature.
- `blocks` — declared context block names. Blocks are populated at runtime, not authored here; this section only registers which names are legal.

---

## 3. Builder contract

The builder assembles the final message set. Keep the model-side half of capability 6 intact: the model must still be able to inspect and manage its context blocks even though the *static text* comes from YAML.

```python
class PromptSet:
    """Immutable, agent-scoped view of the loaded registry."""

    def system(self) -> str: ...
    def render(self, key: str, **params: Any) -> str: ...
    def declared_params(self, key: str) -> frozenset[str]: ...
    def keys(self) -> frozenset[str]: ...
```

Assembly order for one agentic call:

| Position | Source | Mutable at runtime |
|---|---|---|
| system | `PromptSet.system()` | no |
| context blocks | `self.context.blocks[...]` | yes — developer and model |
| event history | harness-managed | append-only |
| task instruction | `PromptSet.render(key, **params)` | no |
| typed params | method arguments | per call |

Requirements:

- `render` receives typed values and does its own coercion. Callers must not pass pre-formatted strings.
- Rendering a key with params that do not match `declared_params` raises. Fail at call time, not silently.
- The rendered text and the resolved key both go into the trace span, so a run can be replayed against a pinned registry version.
- Context blocks stay model-callable — `self.context.blocks.keys()`, assignment, and deletion must all still work. Only static text moved to YAML.

Method wiring:

```python
@agentic(prompt="support.classify")
async def classify(self, message: str) -> TicketKind:
    """Classify an inbound message. Documentation only — not sent to the model."""
    ...
```

The `@agentic` decorator resolves `self.prompts.render("support.classify", message=message)` for the task instruction and leaves everything else to the harness.

---

## 4. CI drift test

This replaces the drift protection that co-located prompts provide for free. It is not optional.

Assert bidirectionally, so neither side can drift:

```python
def test_prompt_contract():
    registry = PromptRegistry.load("prompts/")

    for cls in all_agent_classes():
        pset = registry.for_agent(cls.__name__)

        declared_in_code = {
            m.prompt_key for m in agentic_methods(cls)
        }
        declared_in_yaml = pset.keys()

        # every agentic method has a prompt
        assert declared_in_code <= declared_in_yaml, (
            f"missing prompts: {declared_in_code - declared_in_yaml}"
        )
        # no orphaned prompts
        assert declared_in_yaml <= declared_in_code, (
            f"orphaned prompts: {declared_in_yaml - declared_in_code}"
        )

        # signature params match declared params
        for method in agentic_methods(cls):
            sig_params = frozenset(signature_params(method)) - {"self"}
            yaml_params = pset.declared_params(method.prompt_key)
            assert sig_params == yaml_params, (
                f"{method.prompt_key}: signature {sig_params} != yaml {yaml_params}"
            )
```

Three failure modes it catches:

| Drift | Symptom without the test |
|---|---|
| Method added, prompt not authored | Runtime `KeyError` in production |
| Prompt deleted or renamed in CD | Runtime `KeyError` in production |
| Parameter added or renamed in Python | Template silently drops the variable; model gets an incomplete instruction |

The third is the dangerous one — it fails silently and degrades output quality without raising. Do not ship the registry pattern without this test.

**Additional guard**: a lint rule rejecting string literals over N characters in modules that import the agent base class. This catches prompts creeping back inline.

---

## 5. Injection and lifecycle

```python
# composition root — one place, at startup
registry = PromptRegistry.load(
    path=settings.PROMPT_DIR,
    version=settings.PROMPT_VERSION,   # pinned by CD
)

agent = SupportAgent(
    prompts=registry.for_agent("SupportAgent"),
    order_db=OrderDB(create_engine(settings.DB_DSN)),
)
```

- Load once at process start. Do not reload mid-session.
- `PROMPT_VERSION` comes from the deployment manifest, not from a default in code.
- Fail fast: if a declared key is missing at load time, refuse to start. Do not defer to first call.
- Record the resolved version in every trace so a run can be reproduced.

**Deployment consequence to state when relevant**: prompts can now be changed without a code deploy, which is the point. But the CI contract test runs against a specific registry version — a prompt-only rollout that renames a key or changes a parameter set will break at runtime unless it is gated by the same test. Prompt-only deploys must run the contract test against the target code revision.

---

## 6. Migrating inline prompts

Order matters — do not batch these.

1. **Inventory.** Find every prompt string: literals, f-strings, `.txt`/`.md` reads, template files, DB-sourced prompts. List call site → destination key.
2. **Assign keys.** `<agent>.<method>` by default. Keys are permanent; choose carefully.
3. **Move text verbatim first.** Copy exactly, no rewording. A migration that also edits prompts cannot be A/B verified.
4. **Convert interpolation to declared params.** Every `{var}` or `{{ var }}` becomes an entry in `params`. Interpolation of pre-formatted strings becomes a typed parameter plus builder-side formatting.
5. **Wire `@agentic(prompt=...)`.** Delete the inline string in the same commit — never leave both.
6. **Add the contract test.** Before the migration PR merges, not after.
7. **Verify output parity.** Same inputs, compare rendered prompt text byte-for-byte against the pre-migration version. Only then start editing prompts.
8. **Add the lint rule** blocking new inline prompt literals.

Step 3 and step 7 exist to keep the migration behavior-preserving. If a prompt needs rewording, that is a separate PR after parity is confirmed.
