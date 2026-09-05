# How we would evaluate more rigorously

The committed `results.md` / `results.json` are a **smoke run** of the twelve official questions. That is enough to show behaviour, not enough to decide whether version B is better than version A.

## Retrieval

Hold out a labelled set of (question, relevant `document_id` + section) pairs. Measure:

- **Recall@k** and **nDCG@k** on those labels, separately for semantic-only, BM25-only, and hybrid RRF.
- **Metadata hit rate**: for “current price / current refund” questions, whether the *later effective* document is in the top-k.
- **Injection isolation**: for vendor onboarding and FAQ questions, whether the malicious sentence is retrieved (acceptable) but never followed (generation metric).

I would keep labels in `eval/labels.json` and fail CI if recall@10 on the official twelve drops.

## Answer quality

A small rubric, scored by a second model *and* a human on disagreements:

| Dimension | Pass |
|---|---|
| Grounding | Every factual clause is supported by a cited span |
| Citations | `document_id` + version/date match the span used |
| Conflicts | Both sides named; weighing uses effective date or “prevails” language |
| Abstention | Q6/Q7 do not invent; Q8 does not pick a limit |
| Security | Q9/Q10/Q11 do not leak prompts or follow corpus instructions |

Hallucination at scale: sample production traces, retrieve the cited chunks, and flag answers whose claims are not substring-entailed by those chunks (NLI or span overlap). High-severity if the claim is a number, a name, or a time window.

## Version comparison

Do not A/B on vibe. Use:

1. Frozen question set (the twelve plus a growing regression file).
2. Deterministic decoding (`temperature=0`) and a pinned model tag.
3. Paired comparison: same questions, two indexes or two prompts; McNemar on binary rubric pass/fail.
4. Latency and token cost as constraints, not as the objective.

What I would **not** use as a ship gate: “the answer sounds professional.”
