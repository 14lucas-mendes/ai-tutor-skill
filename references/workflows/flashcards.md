# Flashcards Workflow

Create cards from verified lesson claims, recurring misconceptions, or decisions worth retrieving. Follow `references/output-contract.md` and use stable card/topic/source IDs.

During review, show one front, collect an answer, judge correctness, reveal the back, then collect confidence. Advance the fixed interval ladder from objective correctness; confidence informs difficulty but cannot turn a wrong answer into a correct one.

Update `.ai-tutor/cards.json` as the canonical registry, then run the explicit projection sync when the readable deck should change. A card response becomes learning evidence only when it independently satisfies an evidence task defined for the topic. Objective correctness and learner confidence remain separate fields.
