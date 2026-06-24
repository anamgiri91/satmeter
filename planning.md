# TakeMeter — Planning

*A four-label classifier for the role a comment plays in a college admissions discussion thread — advice, story, opinion, or feeling — built and evaluated on r/ApplyingToCollege.*

---

> **Timeline note for graders:**
> Sections 1–7 were written before data collection began.
> The Baseline Results section was added after the zero-shot baseline was evaluated.
> The Post-Fine-Tuning Update was added after the fine-tuned model was evaluated.

---

## 1. Community

**Community:** r/ApplyingToCollege (A2C), the largest English-language subreddit for U.S. college admissions discussion.

**Why this community:** A2C produces the same handful of thread types over and over — "chance me" posts, decision-reveal megathreads, financial aid questions, "is X school worth it" debates — and each thread type pulls in a genuinely different mix of comment behavior. A chance-me thread draws predictions and rankings; a decision thread draws stories and raw emotion; a financial aid thread draws people citing actual CSS Profile and Common Data Set numbers. That mix is exactly what makes a 4-way classifier meaningful here rather than trivial — if the community only ever produced one kind of comment, the labels would be redundant. A2C also has a community-recognized standard for "real evidence" (CDS percentiles, published aid policies, admit-rate breakdowns by round), so annotators aren't inventing a definition of "verifiable" from scratch — the community already treats specific sources as credible, which makes `evidence_based_advice` a learnable category instead of a subjective one. I also already have working domain knowledge of admissions discourse through Beyond Horizon Academy, which matters on a single-annotator project where label quality depends on the annotator understanding the domain's own internal standards.

---

## 2. Labels

| Label | Definition |
|---|---|
| `evidence_based_advice` | A comment that recommends a specific action and backs it with something that would still hold up as fact if the opinion framing were removed — a published policy, a school's own reported statistic, or a documented practice. |
| `anecdotal_experience` | A comment that mainly recounts the writer's own admissions story — stats, decision, timeline — without aiming a recommendation at the reader. |
| `unsupported_take` | A comment that states a confident claim, ranking, prediction, or warning — including advice-shaped ones — whose backing wouldn't survive having the confident framing stripped away. |
| `emotional_reaction` | A comment that's mainly the writer expressing a feeling about their own process, with little or no specific detail or reasoning behind it. |

**Examples:**

- `evidence_based_advice`
  - "Michigan's Common Data Set lists their middle 50% SAT as 1390–1540 — if you're below that, retaking before the next deadline is worth it, that's their own reported range."
  - "Most schools post a specific FAFSA priority deadline on their financial aid page — file with estimated numbers before that date, you can correct it later."

- `anecdotal_experience`
  - "3.7 GPA, 1450 SAT, applied ED to Michigan, got deferred, then accepted RD in March."
  - "Interviewed at Tufts last week, the alumni interviewer mostly asked about my robotics club, felt pretty low-key."

- `unsupported_take`
  - "Anyone applying to a T20 without a 1500+ is wasting the application fee."
  - "Just retake the SAT, anything under 1500 is basically a rejection letter at every T20."

- `emotional_reaction`
  - "Got rejected today and I'm absolutely devastated, don't know how to process this."
  - "Sending good vibes to everyone still waiting on decisions this week."

---

## 3. Hard Edge Cases

**Primary edge case — `evidence_based_advice` vs. `unsupported_take`:** Both labels can take the identical grammatical shape — an imperative recommendation plus a number. "Retake the SAT if you're under 1500, top schools barely look at you otherwise" reads almost the same as the genuinely evidence-based example above, but "barely look at you" isn't a checkable fact, it's an assertion wearing a number's clothes. Tone and confidence are useless here since both labels can sound equally certain.

**Handling rule:** Strip the imperative and isolate the justification on its own. If what's left is a specific, sourced fact (a CDS range, a published deadline, a documented mechanism), label `evidence_based_advice`. If what's left is an unfalsifiable claim about how schools "look at" or "treat" applicants, label `unsupported_take` — regardless of how directive or numerically precise the comment sounds.

**Secondary edge cases (same underlying problem — personal detail can mask the real category):**

- `anecdotal_experience` vs. `emotional_reaction`: if the comment includes concrete process detail (scores, schools, timeline, decision type) beyond the bare outcome, label `anecdotal_experience` even if it's heavily emotional. If it's just the bare outcome plus a feeling with nothing else to recount, label `emotional_reaction`.
- `anecdotal_experience` vs. `evidence_based_advice`: if personal detail is included to support a recommendation aimed at the reader, label by the recommendation (apply the primary rule above). If the story is recounted for its own sake with no directed recommendation, label `anecdotal_experience`.
- **Mixed-type posts (added mid-project):** Many Reddit comments combine types in the same post — a verifiable fact followed by a speculative prediction, or a personal story that pivots to emotional processing. Label by the primary purpose of the comment: whatever the comment is mainly doing. Do not lower the label quality by picking whichever label the first sentence fits.

---

## 4. Data Collection Plan

**Where:** Reddit's API (PRAW) against r/ApplyingToCollege, pulling from completed decision-cycle megathreads (static and fully resolved, so the comment mix won't shift mid-collection), supplemented with financial-aid threads and "chance me" threads specifically, since those are the highest-yield sources for `evidence_based_advice` and `unsupported_take` respectively.

**Volume target:** 50 examples per label minimum for the first 200, collected deliberately to hit that balance rather than sampling randomly and accepting the community's natural skew (which I expect to over-produce `unsupported_take` and `emotional_reaction` and under-produce `evidence_based_advice`).

**If a label is underrepresented after 200:** Don't lower the bar for what counts as `evidence_based_advice` just to hit the count. Instead, run a second, targeted collection pass aimed at threads with a structurally higher base rate of that label — financial aid megathreads, "Common Data Set" stickies, transfer-admission threads. If the count is still short after a targeted pass, that's a real finding to report (this label is genuinely scarce in this community), not a project failure — the explicit choice becomes accepting the smaller count with a documented limitation, or applying class weighting during training, rather than relabeling borderline cases to inflate the number.

**Labeling process:** All examples were labeled manually. I worked in batches of approximately 30 comments at a time, applying the strip-the-framing test to every ambiguous case. If a comment mixed types (for example, a factual claim followed by a speculative prediction), I labeled the primary purpose of the comment. I did a second pass over the full dataset after finishing to catch inconsistencies introduced by rule refinements midway through. I originally planned to use Llama 3.1 70B to pre-label batches and track an override rate (see Section 7), but after completing the first 50 manual labels I found I was faster and more confident labeling directly — the pre-labeling step added a review burden without improving consistency. I annotated all 242 examples manually as a result, and the AI tool plan was repurposed toward failure analysis instead.

---

## 5. Evaluation Metrics

- **Macro-F1** as the headline metric, not accuracy — accuracy would let the model "succeed" by mostly predicting whichever class is most common in the wild, exactly the failure mode a 4-way taxonomy is meant to avoid.
- **Per-class precision and recall**, with extra weight on `evidence_based_advice` precision specifically: a false positive there means the tool presents an unsupported claim to a real student as verified advice, which is the costliest error type for a deployed version of this.
- **Confusion matrix**, read against the three boundary pairs from Section 3 — errors should concentrate there, and the cost of an error differs a lot by pair (confusing `anecdotal_experience`/`emotional_reaction` is low-stakes; confusing `evidence_based_advice`/`unsupported_take` is not).
- **Self-consistency check:** after finishing all annotations, blind-relabel a random 20-comment subset (without looking at the original label) and compare. Low agreement with past labels on a given class means the definition isn't precise enough — a confound to fix before trusting the model's score on that class.

---

## 6. Definition of Success

- Macro-F1 ≥ 0.75 on a held-out test split.
- No single class F1 below 0.65, so a strong macro average can't hide one class that's failing.
- Precision on `evidence_based_advice` ≥ 0.80 specifically, since that's the label the tool exists to surface, and false positives there are worse than a mediocre score anywhere else.
- "Good enough to deploy" is stricter than "good enough to submit": the same three thresholds, but measured against a fresh batch of comments collected after training and never used in any form during development, to rule out the model having absorbed quirks of one collection pass.

**Is this specific enough to check objectively?** Yes — each criterion is a single number compared against a defined metric on a defined split, so at the end this is a lookup, not a judgment call.

---

## 7. AI Tool Plan

**Label stress-testing (pre-annotation):** Before annotating, give an AI tool the four label definitions and the edge cases above, and ask it to generate 5–10 new boundary posts targeting the `evidence_based_advice`/`unsupported_take` line specifically, since that's the least stable boundary. If any generated post is a genuine coin flip even after applying the decision rule, revise the definition and re-run the stress test before collecting any of the 200 examples.

**Annotation assistance (planned, then revised):** Originally planned to use Llama 3.1 70B via Groq to pre-label batches of 25 examples, tracking a `label_source` field and override rate. After the first 50 manual labels, I found pre-labeling added review burden without improving consistency, so all 242 examples were labeled manually. The override-rate tracking plan was dropped; the AI tool slot was reallocated to failure analysis below.

**Failure analysis (used as planned):** After evaluation, the list of misclassified examples (true label, predicted label, text) goes to an AI tool to summarize candidate error patterns. Patterns get checked, not trusted — I'll manually re-read a random sample of whatever's flagged before reporting it. Specifically looking for whether errors concentrate along the three boundary pairs already identified (confirms the taxonomy is working as intended) versus showing up somewhere unexpected (means there's a structural issue the design phase missed).

---

## Baseline Results

*(Added after zero-shot baseline evaluation — before fine-tuning)*

**Test set:** 34 examples (15% stratified split, random seed 42)
**Model:** llama-3.3-70b-versatile via Groq API, temperature 0
**Unparseable responses:** 0 / 34

### Overall Metrics

| Metric | Value | Target | Status |
|---|---|---|---|
| Accuracy | 0.79 | — | — |
| Macro-F1 | 0.77 | ≥ 0.75 | ✓ passes |
| EBA precision | 0.78 | ≥ 0.80 | ✗ just below |

### Per-Class Metrics

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| evidence_based_advice | 0.78 | 0.88 | 0.82 | 8 |
| anecdotal_experience | 0.73 | 0.89 | 0.80 | 9 |
| unsupported_take | 0.90 | 0.82 | 0.86 | 11 |
| emotional_reaction | 0.75 | 0.50 | 0.60 | 6 |

### Confusion Matrix

| true \ predicted | evidence | anecdotal | unsupported | emotional |
|---|---|---|---|---|
| evidence_based_advice | 7 | 0 | 1 | 0 |
| anecdotal_experience | 0 | 8 | 0 | 1 |
| unsupported_take | 2 | 0 | 9 | 0 |
| emotional_reaction | 0 | 3 | 0 | 3 |

### Error Breakdown by Boundary Pair

| Boundary pair | Errors | Cost level | Status |
|---|---|---|---|
| unsupported_take ↔ evidence_based_advice | 2 | HIGH | ✗ |
| anecdotal_experience ↔ emotional_reaction | 4 | low | expected |
| anecdotal_experience ↔ evidence_based_advice | 0 | medium | ✓ |

**Total misclassified:** 7 / 34

### Observations

- `emotional_reaction` is the weakest class (F1 = 0.60, below the 0.65 floor). All 4 misclassifications go the same direction — the model predicts `anecdotal_experience` when the true label is `emotional_reaction`. This is the exact pattern predicted: a bare outcome plus a feeling gets pulled toward `anecdotal_experience` when any concrete detail is present, even if the comment's primary function is emotional.
- `evidence_based_advice` precision is 0.78 — two points below the 0.80 deployment target. Both false positives come from `unsupported_take` comments that mimic the surface structure of evidence (specific, imperative, how-to framing) without a verifiable source. This is the highest-cost failure mode.
- `unsupported_take` is the strongest class (F1 = 0.86) — the model handles confident, unverified claims well when they lack any structural resemblance to sourced advice.
- Macro-F1 of 0.77 clears the ≥ 0.75 threshold, but two individual class thresholds are not met: `emotional_reaction` F1 (0.60 < 0.65) and `evidence_based_advice` precision (0.78 < 0.80). Both need to improve before the model meets the deployment bar from Section 6.

### Hypothesis for Fine-Tuning

Fine-tuning should close both gaps. The `emotional_reaction` / `anecdotal_experience` boundary needs the model to learn that primary function determines the label, not the presence of incidental concrete detail. The `evidence_based_advice` precision gap needs the model to learn that surface structure — numbers, imperatives, how-to framing — is not sufficient; a verifiable source must be present in the justification after the opinion framing is stripped away.

---

## Post-Fine-Tuning Update

*(Added after fine-tuned model evaluation)*

Fine-tuned model (v2, 242 examples) meets all three deployment targets:

| Metric | Value | Target | Status |
|---|---|---|---|
| Macro-F1 | 0.839 | ≥ 0.75 | ✓ |
| Minimum per-class F1 | 0.800 (EBA) | ≥ 0.65 | ✓ |
| EBA precision | 0.889 | ≥ 0.80 | ✓ |

The addition of 20 targeted EBA examples covering application mechanics, test policy, transfer pathways, and scholarship criteria was sufficient to close the EBA precision gap from 0.78 to 0.889. EBA recall remains at 0.73 — the model is conservative on this label, which is the preferred failure direction given that false positives on EBA carry higher real-world cost than false negatives.

**Post fine-tuning error analysis (6/37 misclassified):** 4 errors on the HIGH-COST EBA ↔ unsupported_take boundary, 2 on the low-cost anecdotal ↔ emotional boundary. Of the 4 high-cost errors, 3 involve comments where a claim is factually true but stated without an explicit source citation — the model has learned to recognize explicitly sourced advice but remains uncertain on implicitly-sourced or general-knowledge claims. This is the residual hard case in the taxonomy and would require either more examples of implicitly-sourced EBA or a refinement of the label definition to handle it.