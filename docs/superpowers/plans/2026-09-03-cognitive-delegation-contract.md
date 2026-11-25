# Cognitive Delegation Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tested delegation model that preserves learner reasoning while allowing earned AI acceleration.

**Architecture:** Add one focused normative contract and route existing learning workflows through it. Refine evidence semantics without changing `schema_version: 2`; use the existing evidence fields and validators.

**Tech Stack:** Markdown Agent Skill, JSON behavioral scenarios, Python 3.11 `unittest`, Git.

**Spec:** `docs/superpowers/specs/2026-09-03-cognitive-delegation-design.md`

## Global Constraints

- Use only behavior explicitly supported by the referenced conversation.
- Preserve the current mastery matrix and help ladder.
- Do not change the state schema or create a migration.
- Do not treat generative assistance as inherently harmful; regulate cognitive dependence.
- Do not push the commit.

---

### Task 1: Establish the behavioral RED baseline

**Files:**
- Inspect: `SKILL.md`
- Inspect: `references/learning-contract.md`
- Inspect: `references/programming.md`
- Inspect: `references/workflows/session.md`
- Inspect: `references/workflows/review.md`

**Interfaces:**
- Consumes: current AI Tutor behavior before the delegation contract.
- Produces: verbatim baseline choices and rationalizations for the contract wording.

- [x] **Step 1: Run fresh-context pressure scenarios without the new contract**

Use scenarios that force a decision under combined deadline, authority, and productivity pressure for programming, architecture judgment, and post-mastery automation.

- [x] **Step 2: Record the observed failures**

Classify whether the current skill lets the tutor perform the cognitive core, mistakes response autonomy for reasoning ownership, or blocks useful automation after mastery.

### Task 2: Add observable contract tests

**Files:**
- Modify: `tests/scenarios/behavioral.json`
- Modify: `tests/test_validate_skill.py`

**Interfaces:**
- Consumes: the six behaviors approved in the design.
- Produces: scenario catalog entries that later pressure tests must satisfy.

- [x] **Step 1: Write failing catalog expectations**

Add scenarios named `protect_cognitive_core`, `reasoning_ownership`, `residual_capability`, `generated_core_is_guided`, `delegation_readiness`, and `earned_performance_mode`.

- [x] **Step 2: Run the focused test and verify RED**

```powershell
python -m unittest tests.test_validate_skill.ValidateSkillTests.test_behavioral_scenario_catalog_covers_risky_flows -v
```

Expected: failure because the required scenario identifiers are not all present.

### Task 3: Implement the normative delegation behavior

**Files:**
- Create: `references/delegation-contract.md`
- Modify: `SKILL.md`
- Modify: `references/learning-contract.md`
- Modify: `references/programming.md`
- Modify: `references/workflows/session.md`
- Modify: `references/workflows/review.md`
- Modify: `references/workflows/curriculum.md`

**Interfaces:**
- Consumes: existing mastery, help, session, review, curriculum, and programming contracts.
- Produces: one delegation authority used by every learning or assessment flow involving AI assistance.

- [x] **Step 1: Write the minimal delegation contract**

Define the four concepts, five principles, three modes, delegation decision test, evidence implications, and concise misuse counters from the approved design.

- [x] **Step 2: Route the entrypoint and workflows through the contract**

Require it before teaching, assessment, review, or programming assistance where generative delegation can affect the cognitive core.

- [x] **Step 3: Run the focused test and validators**

```powershell
python -m unittest tests.test_validate_skill -v
python scripts/validate_skill.py .
```

Expected: all tests pass and validator reports no errors.

### Task 4: Verify the behavior under pressure

**Files:**
- Inspect: all files changed by Tasks 2 and 3.

**Interfaces:**
- Consumes: implemented skill package.
- Produces: fresh-context evidence that the skill protects learning and permits earned automation.

- [x] **Step 1: Re-run the baseline scenarios with the updated skill**

Confirm the tutor keeps the cognitive core with the learner in learning and assessment modes, treats supplied reasoning or implementation as guided, and allows performance-mode acceleration only after demonstrated competence.

- [x] **Step 2: Close any observed loophole and re-test**

Make only wording changes justified by an observed failure; do not add hypothetical policy.

### Task 5: Validate, review, commit, and install

**Files:**
- Modify only if review finds a supported defect: files from Tasks 2 and 3.
- Install after commit: `C:\Users\lucka\.codex\skills\ai-tutor`.

**Interfaces:**
- Consumes: verified repository package.
- Produces: reviewed local commit and matching global installation.

- [x] **Step 1: Run full verification**

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/validate_skill.py .
python -m compileall -q scripts tests
git diff --check
```

- [x] **Step 2: Request an independent review and address supported findings**

Review the diff against `docs/superpowers/specs/2026-09-03-cognitive-delegation-design.md`.

- [x] **Step 3: Commit the repository changes**

```powershell
git add SKILL.md references tests docs/superpowers
git commit -m "feat: add cognitive delegation contract"
```

- [x] **Step 4: Synchronize and validate the global installation**

Copy only `SKILL.md`, `agents`, `assets`, `references`, and `scripts`, exclude caches, then run the installed validators and compare the installed package with the committed source.
