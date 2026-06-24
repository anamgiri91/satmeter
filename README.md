# TakeMeter

TakeMeter is a four-class text classifier for Reddit college admissions comments.

The main idea is simple: when students read advice online, it is hard to tell what is actually useful and what is just someone being confident. On r/ApplyingToCollege, people give advice, share their own results, make strong claims, and sometimes just vent. TakeMeter tries to sort those comments into four categories so readers can better understand what kind of comment they are looking at.

The four labels are:

* `evidence_based_advice`
* `anecdotal_experience`
* `unsupported_take`
* `emotional_reaction`

My goal was not to decide whether a comment is "good" or "bad." I wanted to classify the role the comment plays in the conversation.

---

## What I Built

I built and fine-tuned a DistilBERT model to classify college admissions comments from r/ApplyingToCollege.

The full pipeline had three main parts:

1. I collected and manually labeled 242 Reddit comments.
2. I created a zero-shot baseline using Llama-3.3-70B through the Groq API.
3. I fine-tuned `distilbert-base-uncased` using Hugging Face `transformers` on Google Colab.

The fine-tuned model used a 70/15/15 train, validation, and test split with stratified labels and random seed 42.

What surprised me most was that the smaller fine-tuned DistilBERT model performed almost the same as the much larger Llama baseline. It matched the baseline accuracy and slightly improved macro-F1, even though it is much smaller and runs locally.

---

## Community Choice and Reasoning

I chose r/ApplyingToCollege because the advice quality problem there is unusually clear and consequential. Students making decisions about where to apply are reading hundreds of comments from strangers, and there is almost no signal about whether a given comment is grounded in documented fact or just confident speculation. The four epistemic categories I defined map directly onto the kinds of posts that appear there, and the community is large enough that I could collect 242 labeled examples fairly quickly. Unlike a general discussion forum, r/ApplyingToCollege also has a narrow enough topic that the label boundaries remain stable across comments — "evidence" in this context almost always means admissions statistics, school policies, or financial aid rules, which made annotation more consistent.

---

## Label Definitions

### `evidence_based_advice`

A comment that recommends a specific action AND backs it with something that would still hold up as fact if the opinion framing were removed — a published policy, a school's own reported statistic, or a documented practice.

**Example 1:**
> "Some schools don't consider your freshman year GPA. I would apply specifically to those schools."

The advice ("apply to those schools") is grounded in a real and documented institutional policy, not a guess about how admissions works.

**Example 2:**
> "Everyone who files the FAFSA is at least eligible for up to $5500 in federal direct student loans the first year, $6500 the second, and $7500 the third and fourth year, regardless of family income."

The specific dollar figures and progression are documented federal policy. Stripping the framing leaves a verifiable fact.

---

### `anecdotal_experience`

A comment that mainly recounts the writer's own admissions story — stats, decisions, timeline — without aiming a recommendation at the reader.

**Example 1:**
> "I wrote my Princeton Essay on Obi Wan Kenobi and the Star Wars high ground theory, which was amazing to write about and totally something I would do again in a heartbeat."

The writer is sharing what they personally did, not telling the reader what to do.

**Example 2:**
> "I chose the state school I got a full ride at that has a good program for my career. I'm going to be a pharmacist, not a quant, so getting $100k in loans for undergrad didn't make sense for me."

This is a first-person account of a personal decision and the reasoning behind it — not general advice.

---

### `unsupported_take`

A comment that states a confident claim, ranking, prediction, or warning — including advice-shaped ones — whose backing would not survive having the confident framing stripped away.

**Example 1:**
> "For entrepreneurship look at Penn maybe. They tend to have higher acceptance rates out of the Ivies and have a great business school for undergrad."

Strip the framing: "Penn tends to have higher acceptance rates out of the Ivies." This is not a documented fact — it is an impression the writer holds that could easily be wrong or outdated.

**Example 2:**
> "Going from a 2.85 to a 4.0 from one year to the next is also a serious turn around. OP needs a fantastic essay and to really sell their ECs but imo they have a shot."

The prediction ("they have a shot") is stated with confidence but has no sourced basis. Admissions outcomes for a specific profile cannot be predicted this way.

---

### `emotional_reaction`

A comment that is mainly the writer expressing a feeling about their own process, with little or no specific detail or reasoning behind it.

**Example 1:**
> "Got rejected today and I don't know how to process this. Sending good vibes to everyone still waiting on decisions."

The entire comment is an emotional response to a personal event. There is no advice or outcome description.

**Example 2:**
> "I'm trying to squeeze in so many last minute ECs as a senior oh god I hope they work out."

The writer is expressing anxiety about their own situation, not recounting what happened or advising anyone.

---

## My Main Labeling Rule

The hardest boundary was between `evidence_based_advice` and `unsupported_take`.

The rule I used was:

Strip away the confident wording and look at the reason behind the claim.

If the reason is specific and verifiable — a school's published policy, a documented statistic, a federal regulation — I labeled it `evidence_based_advice`.

If the reason is mostly a belief, prediction, or assumption about how admissions works, I labeled it `unsupported_take`.

This helped a lot because many unsupported comments sound very confident, and many evidence-based comments also sound confident. The tone alone was not enough.

---

## Data

**Source:** r/ApplyingToCollege — comments collected manually by browsing threads about GPA, test scores, financial aid, applications, and admissions decisions.

**Labeling process:** I labeled all 242 comments myself directly in a CSV file. I worked in batches of about 30 comments at a time, applying the strip-the-framing test to every comment I was unsure about. If a comment mixed types (for example, a factual claim followed by a speculative prediction), I labeled the primary purpose of the comment — whatever it was mainly doing. I did a second pass over the full dataset after finishing to catch any inconsistencies introduced by labeling rule refinements midway through.

**Label distribution:**

| Label                   | Total |
| ----------------------- | ----: |
| `evidence_based_advice` |    70 |
| `anecdotal_experience`  |    58 |
| `unsupported_take`      |    76 |
| `emotional_reaction`    |    38 |

The biggest weakness in the dataset is that `emotional_reaction` had the fewest examples. It only had 38 total examples and 6 examples in the test set, so the results for that label are not as reliable as the others.

---

## Difficult Annotation Examples

### Difficult Example 1 — Evidence embedded in opinion

> "We reject around 75% of all 1600's. Lots of these kids have perfect GPAs. So the answer is no and it's not even close."

This was hard because the first sentence ("We reject around 75% of all 1600's") sounds like it could be a cited statistic from an admissions officer. But the framing "the answer is no and it's not even close" is pure confident assertion. I applied the strip test: if I remove the confident framing, what remains is a specific rejection-rate figure — something that, if the writer really is an admissions professional citing their own institution's data, is a real fact. I labeled this `evidence_based_advice` because the underlying claim is specific enough to be falsifiable. If the same comment had said "lots of perfect scorers get rejected" without the number, it would have been `unsupported_take`.

### Difficult Example 2 — Personal experience that sounds like advice

> "As someone who's been through the college process I really do recommend taking this post seriously. I didn't start on college recommendations until two months before my applications were due and it cost me a lot of unnecessary stress."

This was a close call between `anecdotal_experience` and `evidence_based_advice`. The writer is recommending an action ("take this seriously," "start early") but the backing is their own personal mistake, not a documented rule. I labeled it `anecdotal_experience` because stripping the recommendation leaves only a personal story — there is no independently verifiable fact behind it. The decision rule I used: if the justification for the advice is "I went through this," it's anecdotal, even if it's framed as a recommendation.

### Difficult Example 3 — Emotional comment with a factual detail

> "I got my first EA decision back and it's a rejection highlighting that it's caused by the financial aid request. They said if my financial situation changes I can contact them to reopen my case. The reality of college admissions as an international student I guess."

This could have been `anecdotal_experience` because the writer is recounting what happened to them. But the last sentence — "The reality of college admissions as an international student I guess" — shifts the register from reporting an outcome to expressing resignation and frustration. The primary purpose is emotional processing, not outcome description. I labeled it `emotional_reaction`. The rule I used: if the comment ends by expressing a feeling about the situation rather than completing a narrative, it tips toward `emotional_reaction`.

---

## Training Setup

**Fine-tuned model:**

* Base model: `distilbert-base-uncased`
* Task: sequence classification (4 classes)
* Platform: Google Colab (T4 GPU)
* Library: Hugging Face `transformers`
* Max token length: 256
* Split: 70/15/15 train/val/test, stratified by label, random seed 42

**Key hyperparameter decision — max token length:** I set `max_length` to 256 rather than the DistilBERT default of 512. After tokenizing the training set, the 95th percentile of token lengths was well below 200. Padding every sequence to 512 would have doubled memory usage and training time with no benefit, since the extra positions would all be padding tokens. 256 covers every comment in the dataset while keeping training fast on a free Colab instance.

**Baseline:**

* Model: Llama-3.3-70B (via Groq API)
* Prompting: zero-shot, temperature=0
* Same label definitions as annotation rules

I wanted the baseline to be fair, so I gave it the same definitions I used while labeling the data.

**Baseline prompt used:**

```
You are a classifier for comments from r/ApplyingToCollege.
Classify each comment into exactly one of these four labels:

evidence_based_advice
  A comment that recommends a specific action AND backs it with something
  that would still hold up as fact if the opinion framing were removed —
  a published policy, a school's own reported statistic, or a documented practice.

anecdotal_experience
  A comment that mainly recounts the writer's own admissions story —
  stats, decision, timeline — without aiming a recommendation at the reader.

unsupported_take
  A comment that states a confident claim, ranking, prediction, or warning
  — including advice-shaped ones — whose backing would not survive having
  the confident framing stripped away.

emotional_reaction
  A comment that is mainly the writer expressing a feeling about their own
  process, with little or no specific detail or reasoning behind it.

Decision rule for evidence_based_advice vs unsupported_take:
Strip the imperative and isolate the justification on its own.
If what remains is a specific, sourced fact (a CDS range, a published
deadline, a documented mechanism), output evidence_based_advice.
If what remains is an unfalsifiable claim about how schools treat
applicants, output unsupported_take — regardless of how directive or
numerically precise the comment sounds.

Output ONLY the label name. No explanation, no punctuation, no extra text.
Valid outputs: evidence_based_advice | anecdotal_experience | unsupported_take | emotional_reaction
```

---

## Results

The fine-tuned DistilBERT model reached the same accuracy as the Llama baseline.

| Metric   | Llama-3.3-70B Baseline | Fine-tuned DistilBERT |
| -------- | ---------------------: | --------------------: |
| Accuracy |                  0.838 |                 0.838 |
| Macro-F1 |                  0.826 |                 0.839 |

The improvement is small, so I would not claim that DistilBERT is clearly better. The test set only had 37 examples, so one prediction changes the numbers a lot.

The honest conclusion is that fine-tuned DistilBERT reached parity with a much larger zero-shot model on this dataset.

That is still meaningful because DistilBERT is much smaller, cheaper, and easier to run locally.

---

## Fine-Tuned Model Performance

| Label                   | Precision | Recall |    F1 | Support |
| ----------------------- | --------: | -----: | ----: | ------: |
| `evidence_based_advice` |     0.889 |  0.727 | 0.800 |      11 |
| `anecdotal_experience`  |     0.889 |  0.889 | 0.889 |       9 |
| `unsupported_take`      |     0.769 |  0.909 | 0.833 |      11 |
| `emotional_reaction`    |     0.833 |  0.833 | 0.833 |       6 |
| **Macro avg**           | **0.845** |  **0.840** | **0.839** |  **37** |

The model did best on `anecdotal_experience`. That makes sense because first-person experience comments usually have clear signals like "I applied," "I got in," "my stats were," or "when I went through this."

The hardest label was `evidence_based_advice`, which had the lowest recall (0.727) — meaning the model missed 3 out of 11 true positives, predicting them as `unsupported_take` instead.

**Baseline per-class metrics (Llama-3.3-70B):**

| Label                   | Precision | Recall |    F1 | Support |
| ----------------------- | --------: | -----: | ----: | ------: |
| `evidence_based_advice` |     0.900 |  0.818 | 0.857 |      11 |
| `anecdotal_experience`  |     0.889 |  0.889 | 0.889 |       9 |
| `unsupported_take`      |     0.769 |  0.909 | 0.833 |      11 |
| `emotional_reaction`    |     0.750 |  0.500 | 0.600 |       6 |
| **Macro avg**           | **0.827** |  **0.779** | **0.795** |  **37** |

The baseline's weakest class is `emotional_reaction` (F1 = 0.600). The fine-tuned model improves that class by 0.233 F1 points — its clearest concrete gain over the baseline.

---

## Confusion Matrix — Fine-tuned DistilBERT

Rows = true label. Columns = predicted label.

| | eba | anec | unsup | emot |
| --- | ---: | ---: | ---: | ---: |
| **evidence_based_advice** | **8** | 0 | 3 | 0 |
| **anecdotal_experience** | 0 | **8** | 0 | 1 |
| **unsupported_take** | 1 | 0 | **10** | 0 |
| **emotional_reaction** | 0 | 1 | 0 | **5** |

*eba = evidence_based_advice, anec = anecdotal_experience, unsup = unsupported_take, emot = emotional_reaction*

The dominant error pattern is `evidence_based_advice → unsupported_take` (3 misclassifications). No other pair accounts for more than 1 error.

---

## Error Analysis

The biggest error pattern was `evidence_based_advice → unsupported_take`, which happened 3 times. That means the model was sometimes too skeptical — it saw assertive language and predicted `unsupported_take` even when the comment had a real factual basis.

### Wrong Prediction 1

> "We reject around 75% of all 1600's. Lots of these kids have perfect GPAs. So the answer is no and it's not even close."
>
> **True label:** `evidence_based_advice` | **Predicted:** `unsupported_take`

The phrase "it's not even close" sounds like pure confident assertion, and the model appears to have weighted that heavily. But the comment leads with a specific rejection-rate figure — the kind of cited statistic the label definition targets. The model focused on the conclusion's tone rather than the factual claim embedded in the first sentence. This is a **training distribution problem**: assertive phrasing is the strongest surface signal for `unsupported_take`, and there are few training examples where assertive framing wraps an actual statistic. More examples of this pattern labeled as `evidence_based_advice` would help.

### Wrong Prediction 2

> "If you are willing to pay full price your odds at most schools will go up significantly. Add MIT, Berkeley, and Duke. MIT fits your profile; Berkeley and Duke don't look at 9th grade. University of Toronto also doesn't look at them and you will get into any program you want there..."
>
> **True label:** `evidence_based_advice` | **Predicted:** `unsupported_take`

"Berkeley and Duke don't look at 9th grade" is a documented admissions policy — a verifiable fact of the kind the label definition requires. But the comment packages it alongside confident predictions ("you will get into any program you want there") that are textbook `unsupported_take`. The model could not separate the factual clause from the surrounding opinion, and labeled the whole comment by its dominant tone. This is a **label granularity problem**: the comment genuinely mixes evidence-based and unsupported content. A stricter annotation rule for mixed-type posts would produce cleaner training signal.

### Wrong Prediction 3

> "I'm taking online dual enrollment courses right now and I have no problem getting As — there's just unnecessary risk I give myself because I need to be more responsible about treating them as actual classes."
>
> **True label:** `emotional_reaction` | **Predicted:** `anecdotal_experience`

The comment contains a reportable outcome ("I have no problem getting As"), which resembles the first-person narrative structure of `anecdotal_experience`. But the main point is a self-evaluation ("unnecessary risk I give myself," "I need to be more responsible") — that is affect, not outcome description. The model keyed on the outcome-shaped first clause and missed the self-critical pivot. This is a **feature limitation**: DistilBERT reads tokens left-to-right in context, but can still be dominated by early signals. The distinction between reporting an outcome and evaluating yourself is semantic, not lexical, and requires more diverse `emotional_reaction` training examples to learn.

---

## Sample Classifications

The following examples were run through the fine-tuned DistilBERT model. Confidence is the softmax probability for the predicted class.

| # | Post (truncated to 150 chars) | Predicted Label | Confidence | Correct? |
|---|---|---|---|---|
| 1 | "Some schools don't consider your freshman year GPA. I would apply specifically to those schools." | `evidence_based_advice` | 0.91 | ✅ |
| 2 | "For entrepreneurship look at Penn maybe. They tend to have higher acceptance rates out of the Ivies..." | `unsupported_take` | 0.88 | ✅ |
| 3 | "Got rejected today and I don't know how to process this. Sending good vibes to everyone still waiting." | `emotional_reaction` | 0.87 | ✅ |
| 4 | "I wrote my Princeton Essay on Obi Wan Kenobi and the Star Wars high ground theory..." | `anecdotal_experience` | 0.83 | ✅ |
| 5 | "We reject around 75% of all 1600's. Lots of these kids have perfect GPAs. So the answer is no..." | `unsupported_take` | 0.74 | ❌ (true: `evidence_based_advice`) |

**On example 1 (correct):** The prediction is reasonable because the comment explicitly references a documented institutional policy ("some schools don't consider your freshman year GPA") and pairs it with a direct recommendation that follows from that fact. Stripping the imperative leaves a verifiable claim — the exact structure the `evidence_based_advice` definition targets.

**On example 5 (incorrect):** The model predicted `unsupported_take` with 0.74 confidence — notably lower than its correct predictions, which suggests genuine uncertainty. The assertive conclusion ("the answer is no and it's not even close") appears to have outweighed the embedded statistic ("we reject around 75% of all 1600's"). This is the dominant failure pattern described in the error analysis above.

---

## What the Model Actually Learned

My original goal was to teach the model an epistemic distinction: is this comment backed by something real, or is it just confident?

But the model mostly learned surface patterns:

* Numbers and school names pushed it toward `evidence_based_advice`.
* First-person past-tense language pushed it toward `anecdotal_experience`.
* Strong confident wording pushed it toward `unsupported_take`.
* Emotional words pushed it toward `emotional_reaction`.

These shortcuts worked most of the time, but they failed when the surface tone and the actual epistemic content disagreed. The clearest example: `evidence_based_advice` comments are often written by people who sound confident precisely because they know the fact they're citing. The model learned to treat confident tone as evidence of `unsupported_take`, which is the opposite of the intended rule.

A second gap: the `emotional_reaction` boundary was defined by the *absence* of reportable content, not the *presence* of emotional vocabulary. The model cannot easily learn from absences — it learned to fire on explicit emotional words, missing comments that expressed feeling through self-critique or minimization rather than direct emotion words.

---

## Spec Reflection

**One way the spec helped:** The explicit strip-the-framing decision rule gave me a repeatable test I could apply during annotation to any ambiguous case. Without it, comments like "Some schools don't consider your freshman year GPA. I would apply specifically to those schools" could plausibly be `unsupported_take` (just someone's opinion about where to apply) or `evidence_based_advice` (a recommendation grounded in a documented policy). The strip test made the right answer unambiguous: removing the imperative leaves a factual institutional policy, so it's `evidence_based_advice`.

**One way implementation diverged:** The spec assumed each comment maps cleanly to a single label. In practice, many r/ApplyingToCollege comments mix types within the same post — a verifiable fact stated, then a speculative prediction appended, then an emotional aside. I handled this by labeling the primary purpose of the comment, but I did not add this "primary purpose" rule to the spec until midway through annotation. Comments labeled in the first third of the project may reflect a slightly different rule than later ones, which likely adds noise to the hardest boundary (evidence vs. unsupported) specifically.

---

## AI Usage

I used AI for two specific parts of the project. I did not use it to label the dataset — all 242 labels were assigned manually.

**Instance 1 — Error pattern identification:** After generating `baseline_errors.csv`, I pasted the 6 misclassified examples into Claude and asked it to identify common themes across the wrong predictions. It surfaced two patterns: (a) all 3 `evidence_based_advice → unsupported_take` errors involved specific statistics or institutional facts embedded inside otherwise opinionated framing, and (b) the `emotional_reaction → anecdotal_experience` errors both involved comments where the writer mentioned a concrete outcome before pivoting to self-reflection. I verified both by re-reading the examples. I kept pattern (a) as-is in my analysis. For pattern (b), I found the explanation partially right but overstated — the emotional register of those comments is distinct even from the first clause, which Claude had glossed over. I qualified that pattern in my own words rather than using Claude's framing.

**Instance 2 — Baseline prompt drafting:** I used Claude to draft an initial version of the Llama classification prompt. The first draft used the phrase "claims backed by evidence," which is too vague — it would have caused the model to label any comment mentioning a number as `evidence_based_advice`, even unverifiable ones. I replaced that language with the strip-the-framing decision rule, which I developed from my own annotation experience. The final prompt language in the "Training Setup" section above is my rewrite, not Claude's draft.

---

## What I Would Improve

The biggest improvement would be collecting more data, especially for `emotional_reaction`.

I would also add more training examples where evidence-based comments are written in a confident tone. That would help the model learn that confidence does not automatically mean unsupported.

I would also improve the labeling rules for mixed comments. A lot of Reddit comments do not fit perfectly into one label. In the future, I would either label the primary purpose of the comment more consistently from the start, or allow multi-label classification.

A better version of this project would probably use at least 500 examples, with a larger test set. With only 37 test examples, the metrics are useful for a class project, but not strong enough to make big claims.

---

## Reflection

This project helped me understand that the hardest part of machine learning is not always the model. In this project, the hardest part was deciding what the labels actually meant.

At first, the four classes sounded simple. But once I started labeling real Reddit comments, I realized how messy online discussion is. People give advice and tell stories in the same comment. They cite facts and then add guesses. They express emotion without using obvious emotional words.

That made the project more useful because it forced me to think carefully about the difference between a label that sounds good and a label that can actually be applied consistently.

TakeMeter is not perfect, but it showed that a small fine-tuned model can learn useful patterns from a small hand-labeled dataset. It also showed me where the model breaks, which is probably the most important part.