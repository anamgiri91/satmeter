# Design & Methodology

How TakeMeter's label taxonomy, evaluation bar, and data strategy were defined *before* any model was trained — and what happened when the baseline missed that bar.

The short version: I set numeric success criteria up front, the zero-shot baseline missed two of them, I diagnosed why from the confusion matrix, made one targeted change, and the fine-tuned model cleared all three. That loop is the actual point of this document.

---

## Why r/ApplyingToCollege

A 4-way classifier is only meaningful if the community actually produces all four kinds of comments in volume — otherwise the labels are redundant. r/ApplyingToCollege works because different thread types pull different comment behavior: "chance me" threads draw predictions, decision threads draw stories and raw emotion, financial-aid threads draw people citing actual Common Data Set numbers. The community also has a shared, pre-existing standard for what counts as "real evidence" (CDS percentiles, published aid policies, admit-rate breakdowns) — so `evidence_based_advice` is a learnable category grounded in the community's own norms, not a definition I had to invent from scratch.

---

## Label Taxonomy & the One Hard Boundary

Four labels, defined in [`README.md`](README.md#the-problem). Three of the four boundaries are fairly separable. One isn't:

**`evidence_based_advice` vs. `unsupported_take`** — both can take the identical grammatical shape: an imperative recommendation plus a number. *"Retake the SAT if you're under 1500, top schools barely look at you otherwise"* reads almost the same as a genuinely evidence-based comment, but "barely look at you" isn't a checkable claim — it's an assertion wearing a number's clothes. Tone is useless here since both labels can sound equally confident.

**Decision rule:** strip the imperative, isolate the justification on its own. If what's left is a specific, sourced fact — a CDS range, a published deadline, a documented policy — label it evidence-based. If what's left is an unfalsifiable claim about how schools "treat" applicants, label it unsupported, regardless of how precise or directive it sounds.

A related problem surfaced mid-annotation: comments that genuinely mix types (a fact, then a speculative prediction, then an emotional aside). The rule adopted was to label the *primary purpose* of the comment rather than whichever type appeared first — a rule I didn't formalize until partway through annotation, which is a documented limitation, not a hidden one (see [README limitations](README.md#limitations)).

---

## Data Collection Strategy

**Target:** roughly balanced volume across all four labels, collected deliberately rather than sampled randomly — a random sample of the subreddit was expected to over-produce `unsupported_take` and `emotional_reaction` and under-produce `evidence_based_advice`, which would bias the classifier before training even started.

**Sourcing:** completed, fully-resolved decision megathreads (so the comment mix wouldn't shift mid-collection), plus financial-aid and "chance me" threads specifically targeted as high-yield sources for the two hardest-to-balance labels.

**If a label stayed underrepresented:** the rule was to run a second, targeted collection pass on structurally higher-yield thread types — not to loosen the label definition just to hit a count. A genuinely scarce label is a real finding to document, not a data problem to paper over.

**Original plan vs. actual:** I'd initially planned to have an LLM pre-label batches of 25 comments and track my override rate as a consistency check. After the first 50 manual labels, pre-labeling was adding review overhead without improving consistency, so I dropped it and labeled all 242 comments by hand. That AI-assist slot was reallocated to post-hoc error analysis instead, where it was actually useful.

---

## Evaluation Design

Set before training, not after:

- **Macro-F1 as the headline metric, not accuracy** — accuracy lets a model "succeed" by defaulting to whichever class is most common, which is exactly the failure mode a 4-way taxonomy exists to catch.
- **`evidence_based_advice` precision weighted separately** — a false positive here means presenting an unsupported claim to a student as verified advice. That's the single costliest error type for any deployed version of this.
- **Errors read against three boundary pairs**, each with an assigned cost level (high / medium / low), so a confusion matrix could be interpreted against real stakes instead of raw counts.
- **A self-consistency check**: blind re-label a random 20-comment subset post-annotation, without looking at the original label. Low agreement on a class means the definition itself isn't precise enough to trust the model's score on it.

### Deployment bar (defined before seeing any results)

| Criterion | Threshold |
|---|---|
| Macro-F1 | ≥ 0.75 |
| Every per-class F1 | ≥ 0.65 |
| `evidence_based_advice` precision | ≥ 0.80 |

Three numbers, checked against a defined split — a lookup, not a judgment call.

---

## Iteration: Baseline → Diagnosis → Fix

**Baseline (zero-shot Llama-3.3-70B) missed two of three thresholds:**

| Metric | Result | Target | Status |
|---|---|---|---|
| Macro-F1 | 0.77 | ≥ 0.75 | passed |
| `emotional_reaction` F1 | 0.60 | ≥ 0.65 | **missed** |
| `evidence_based_advice` precision | 0.78 | ≥ 0.80 | **missed** |

**Diagnosis, from the confusion matrix:**
- All 4 `emotional_reaction` errors went the same direction — misclassified as `anecdotal_experience`. The model was pulling toward "anecdote" whenever any concrete detail was present, even when the comment's primary function was emotional.
- Both `evidence_based_advice` false positives were `unsupported_take` comments mimicking the *surface structure* of evidence (specific, imperative, how-to phrasing) without an actual verifiable source behind them.

**Hypothesis:** fine-tuning on more examples of both patterns — bare-outcome-plus-feeling comments, and confidently-worded-but-unsourced comments — should close both gaps without needing a new labeling rule.

**Result after fine-tuning, +20 targeted `evidence_based_advice` examples:**

| Metric | Baseline | Fine-tuned | Target | Status |
|---|---|---|---|---|
| Macro-F1 | 0.77 | 0.839 | ≥ 0.75 | passed |
| Weakest per-class F1 | 0.60 | 0.800 | ≥ 0.65 | passed |
| `evidence_based_advice` precision | 0.78 | 0.889 | ≥ 0.80 | passed |

All three thresholds cleared. The remaining residual error (4 of 6 post-fine-tuning misclassifications) is comments where a claim is factually true but stated without an explicit citation — the model reliably recognizes *explicitly sourced* advice but is still uncertain on *implicitly sourced* or general-knowledge claims. That's the next boundary to work on, not a solved problem — see [README: What I'd Improve](README.md#what-id-improve-with-more-time).

---

## Full Label Definitions & Edge Cases

For the complete label definitions, examples, and secondary edge-case rules, see the annotation guide this project was built against: [full label spec →](#) *(link to your original planning doc or annotation guidelines file if you keep one in the repo)*.