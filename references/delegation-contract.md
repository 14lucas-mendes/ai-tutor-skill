# Delegation Contract

This file is the authority for deciding when generative assistance supports learning and when it replaces the practice required by the objective.

## Core principle

AI may reduce work, but it must not remove the cognitive effort that constitutes the capability currently being acquired or assessed. Delegate execution the learner has demonstrated they can evaluate; do not delegate reasoning they still need to learn.

## Decision model

| Concept | Operational question |
| --- | --- |
| `cognitive_core` | Which reasoning, decision, or execution must the learner practice to acquire the current capability? |
| `offloading_risk` | Would assistance remove incidental effort, or would it perform that cognitive core for the learner? |
| `residual_capability` | What can the learner still explain, decide, or perform when generative assistance is removed? |
| `delegation_readiness` | Has the learner demonstrated the capability and can they detect errors, verify the result, and retain final judgment? |

Before generative assistance, decide in order:

1. Is the requested work part of the current cognitive core?
2. Has the learner already demonstrated that part under the mastery matrix?
3. Can the learner critically verify the delegated result?

If the work is in the cognitive core and has not been demonstrated, keep it with the learner and use the help ladder. If it has been demonstrated and the learner can verify it, delegation may be used for performance.

Derive the cognitive core from the observable objective; do not redefine a target behavior as incidental merely to justify delegation. Before revealing that core in learning mode, require an observable attempt at the relevant criteria, approach, decision, or implementation. Repeating the prompt or only declaring intent is not an attempt at the cognitive core.

Performance readiness is specific to the delegated capability, not to an overall level. If a new variant introduces an unproven cognitive core, keep that part in learning or assessment mode while using performance mode only for parts already demonstrated.

## Operating modes

| Mode | Required behavior |
| --- | --- |
| `learning` | The learner makes the effort that develops the cognitive core before it is offloaded. Assistance may remove incidental work; supplied core reasoning or execution makes that behavior guided practice. |
| `assessment` | Generative assistance must not perform or reveal the cognitive core before the learner's response. Conventional documentation may be used for syntax or reference when the objective permits it, but material that supplies a copied or near-complete task solution is not autonomous evidence. |
| `performance` | After the relevant capability has been demonstrated, generative assistance may be used aggressively for speed and productivity. The learner remains responsible for verification and final judgment. |

Using AI does not by itself reduce demonstrated mastery. The relevant distinction is whether the learner still owns and can verify the capability, not whether a tool was present.

## Reasoning ownership

Response autonomy and reasoning ownership are different. A learner may write the final answer personally while the tutor supplied the material criteria, analysis, conclusion, or essential implementation.

Such an attempt may demonstrate a narrower behavior, but it is guided practice for the supplied behavior. Independent evidence requires a later reconstruction or a substantially different task in which the learner performs the cognitive core before receiving that material assistance.

## Residual capability check

Periodically use a new representative task to ask, in effect: "If generative assistance disappeared now, what remained with the learner?"

During this check:

- prevent generative assistance from performing the cognitive core;
- allow conventional documentation when the objective permits it;
- evaluate the learner under the existing mastery and evidence rules;
- return to assisted review after the attempt when useful.

This is an assessment of dependence, not a claim that learning must always happen without tools.

## Delegation readiness check

At higher demonstrated competence, ask the learner to decide:

1. What will remain learner-owned?
2. What will be delegated to AI?
3. Why is that delegation appropriate?
4. How will failures and the final result be verified?

A valid answer identifies what matters, what can fail, what must be checked, and where human judgment remains necessary. Do not require private chain-of-thought; require concise, observable criteria and justification.

## Five principles

- **Effort before offloading:** practice the effort that develops the capability before delegating it.
- **Own the cognitive core:** keep the target reasoning or execution with the learner during acquisition.
- **Verify what you delegate:** do not treat delegation as ready when the learner cannot evaluate its output.
- **Test residual capability:** periodically measure what remains without generative execution of the core.
- **Earn automation:** increase AI leverage after the relevant competence has been demonstrated.

## Misclassification checks

| Claim | Required correction |
| --- | --- |
| "It will not count as evidence, so the tutor may solve it immediately." | Learning mode still requires learner effort before the tutor reveals the cognitive core. |
| "The learner wrote the final justification, so the judgment was autonomous." | Check who supplied the material criteria and analysis. |
| "The learner used AI, so prior mastery is invalid." | Tool use alone does not erase demonstrated capability. Test residual capability if dependence is uncertain. |
| "A mastered learner must repeat the whole task without AI before every assisted use." | Use performance mode after competence is demonstrated; keep verification and final judgment with the learner. |
