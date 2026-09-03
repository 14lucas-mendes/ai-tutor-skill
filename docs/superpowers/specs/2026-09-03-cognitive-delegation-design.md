# Cognitive Delegation Design

## Objective

Extend AI Tutor from measuring demonstrated mastery to also regulating when AI delegation preserves or removes the cognitive effort required to acquire a skill.

The design is limited to behavior explicitly stated in the referenced conversation "Simplificar documentação da skill". It does not add research claims, a new state schema, or a migration.

## Existing behavior to preserve

- Require an autonomous attempt before revealing a solution.
- Do not count tutor-provided content or generated media as evidence.
- Keep the mastery thresholds for explanation, application, transfer, repetition, limit detection, and self-correction.
- Use the existing help ladder and evidence model.

## New normative model

Create `references/delegation-contract.md` as the single authority for four concepts:

- **Cognitive Core:** the reasoning or execution the learner must exercise to acquire the current capability.
- **Offloading Risk:** whether delegation removes incidental work or the practice required by the objective.
- **Residual Capability:** what the learner can still explain, decide, or perform when generative assistance is removed.
- **Delegation Readiness:** whether the learner has demonstrated enough competence to delegate and critically verify the result.

The contract must implement the five principles stated in the conversation:

1. Effort before offloading.
2. Own the cognitive core.
3. Verify what you delegate.
4. Test residual capability.
5. Earn automation.

## Operating modes

- **Learning mode:** keep the cognitive core primarily with the learner and apply the help ladder.
- **Assessment mode:** do not let generative assistance perform the cognitive core; conventional documentation may be consulted when the objective permits it.
- **Performance mode:** after competence has been demonstrated, permit aggressive AI assistance for speed while requiring the learner to retain verification and final judgment.

## Evidence semantics

`autonomous` response delivery is not sufficient for independent judgment evidence. When criteria, material analysis, a conclusion, or an essential implementation came from the tutor before the learner produced them, the attempt is guided practice for that behavior.

Independent evidence remains possible through a later reconstruction or a substantially different task in which the learner owns the cognitive core. This is a behavioral refinement of the existing evidence contract, not a schema change.

## Workflow integration

- Session: identify the objective's cognitive core and choose the operating mode before the learning task.
- Review: periodically test residual capability in a new task without generative execution of the cognitive core.
- Curriculum: at higher demonstrated mastery, teach delegation by asking what the learner would delegate, why, how it would be verified, and what judgment remains human.
- Programming: essential tutor-provided code makes the attempt guided when implementation is the assessed capability.

## Verification scope

Add behavioral pressure scenarios for cognitive-core protection, reasoning ownership, residual capability, generated implementation, delegation readiness, and earned performance mode. Run the existing validator and full test suite. Synchronize the verified package to the global installation only after the repository commit.
