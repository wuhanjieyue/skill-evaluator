---
name: skill-evaluator
description: Evaluate portable AI agent skills against production-grade quality gates for trust, reliability, adaptability, convention, effectiveness, installability, packaging, trigger fit, and acceptance readiness. Use when auditing an installed skill folder, reviewing a .skill package before installation, deciding whether a skill is production-ready, or defining the smallest fixes required before publishing or reuse.
---

# Skill Evaluator

Evaluate a skill as an installable production asset. Evidence beats style opinions. Missing evidence fails the gate when the user asks for production readiness.

## Workflow

1. Identify the artifact: installed skill folder, unpacked source directory, or `.skill` package.
2. Run the read-only gate:

```bash
python3 scripts/audit_skill.py --strict /path/to/skill-or-package.skill
python3 scripts/audit_skill.py --self-test
```

3. If the target platform provides its own validator, run it as an additional platform-specific check.

4. Read `SKILL.md`, optional platform metadata such as `agents/openai.yaml`, and only referenced resources needed to explain findings.
5. Score the six dimensions below from evidence.
6. Forward-test when behavior matters: happy path, boundary input, and misuse/non-trigger prompt. Pass only the skill path and task to a fresh agent; do not leak expected answers.
7. Return release status: `PRODUCTION READY`, `CONDITIONAL`, or `BLOCKED`, with one concrete repair or optimization suggestion for every finding.

## Production Gate

Use `BLOCKED` if any item is true:

- `audit_skill.py --strict` fails.
- `audit_skill.py --self-test` fails.
- The target platform's own validator fails when available.
- Any Python script has syntax errors.
- `SKILL.md` has TODO placeholders, missing frontmatter, vague trigger text, or unsupported claims.
- The skill requires secrets, network access, write access, MCP tools, or production systems without naming the dependency and verification path.
- The package cannot be unpacked, copied, discovered, and validated from a clean skill directory.
- Forward tests fail the core job, silently return unusable output, or only pass with leaked context.

Use `PRODUCTION READY` only when all are true:

- Trust and Installability score 5.
- Reliability, Adaptability, Convention, and Effectiveness score at least 4.
- No P0/P1 findings remain.
- The output includes exact verification commands, evidence, and repair suggestions.

Use `CONDITIONAL` for usable but non-production skills. Name the missing evidence.

## Dimensions

Score each dimension from 0-5:

- 5: production-ready evidence.
- 4: strong, minor non-blocking gaps.
- 3: usable with clear limits; not production-ready.
- 1-2: risky or mostly unverified.
- 0: missing, unsafe, or misleading.

### T - Trust

Check whether the skill can be used without unreasonable risk.

- Requests only permissions and external services required by the task.
- Names network, credential, filesystem, destructive, and production-system risks.
- Protects secrets and user data; never asks the agent to reveal hidden tokens.
- Avoids unreviewed remote install pipes unless source, scope, and verification are explicit.
- Scripts are inspectable, scoped, and do not hide side effects.

### R - Reliability

Check whether it works repeatedly under normal, edge, and failure inputs.

- Describes valid inputs, invalid inputs, and expected failure messages.
- Uses deterministic scripts for fragile repeated operations.
- Has the smallest runnable check for non-trivial scripts.
- Produces understandable blocked states instead of silent empty output.
- Behaves from a fresh session, not only after context is primed.

### A - Adaptability

Check whether the agent will invoke it in the right situations.

- `description` states what it does and when to use it.
- Supported inputs, outputs, platforms, and exclusions are explicit.
- Trigger wording avoids broad false positives.
- Variants are routed through references instead of bloating `SKILL.md`.
- The skill asks the user only for information that cannot be safely inferred.

### C - Convention

Check whether another agent can understand, maintain, and install it.

- Folder name, frontmatter `name`, and layout match portable skill conventions.
- Frontmatter uses only `name` and `description`.
- `SKILL.md` stays concise and uses progressive disclosure.
- Optional platform metadata, such as `agents/openai.yaml`, is aligned when present.
- Resource directories exist only when used and are referenced from `SKILL.md`.
- No extra README, changelog, or install guide duplicates skill instructions.

### E - Effectiveness

Check whether the skill actually helps complete the target task.

- Output contract is clear enough to judge success.
- Forward tests cover the core user jobs.
- The result is directly usable, not just more verbose.
- The skill improves quality beyond generic agent behavior.
- Known limits are surfaced before users depend on it.

### I - Installability

Check whether the skill is easy to install, discover, and verify.

- Installs under the target agent's skill directory or a project-local skill directory without path surgery.
- Has no hardcoded user-local paths except documented configuration points.
- Lists required CLIs, APIs, env vars, MCP tools, and restart/new-session needs before first use.
- Supports a clean post-install check: `audit_skill.py --strict`, script self-test, platform validator, or equivalent.
- First prompt after installation should trigger the skill from frontmatter alone.

## Output

Use this format:

```markdown
**Release Status**
BLOCKED | CONDITIONAL | PRODUCTION READY

**Findings**
- [P1] Dimension - evidence-backed problem and impact.
  Fix: smallest concrete change that removes the risk.

**Scores**
| Dimension | Score | Evidence |
| --- | ---: | --- |
| Trust | 0-5 | ... |

**Acceptance Evidence**
- Static gate: command + result
- Self-test: command + result
- Platform validation: command + result
- Forward tests: prompts + result

**Smallest Fixes**
1. Fix ...

**Optimization Suggestions**
- Optional improvement that raises score or confidence without blocking release.
```

If no serious issue is found, say so and list any unverified residual risk.
