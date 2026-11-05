# job-pilot: project notes

Working notes so the project can be resumed on any machine. No private data here.

## Goal
A job-search agent built as a portfolio project for an AI / agentic engineer path.
Security is a core theme, not an add-on. The owner is learning as she builds, so every
step should be understood and defensible in an interview.

## Roadmap
| Stage | What | Status |
|---|---|---|
| 0 | Call the LLM API directly (no frameworks), read usage and `stop_reason` | Done |
| 1 | Matcher: profile + job offer -> classification, score, reasons (structured output) with evals from day one | In progress |
| 2 | Agent loop with tools (find offers) | Todo |
| 3 | Human-in-the-loop + application tracker | Todo |
| 4 | CV / cover-letter adaptation without inventing experience | Todo |
| 5 | Observability, threat model, README, demo | Todo |

Minimum showable: stages 0-2 with evaluation.

## Setup on a new machine
1. `git clone` the repo, then `uv sync` (needs Python 3.11+ and [uv](https://docs.astral.sh/uv/)).
2. Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY` (never commit it).
3. Recreate `data/private/` by hand (git-ignored on purpose):
   - `profile.md`: facts about the candidate, no phone, address, ID or email.
   - `jobs/NN.md`: one file per offer. Top section is the human label
     (`interesa: si | no | quizas` + one-line reason), written BEFORE running anything;
     below `## Oferta` goes the original offer text.
4. Run: `uv run python experiments/stage1_match.py`
   (add `--no-sync` if uv hangs on first start; set `PYTHONUTF8=1` for accents on Windows).

## Decisions so far
- Python + Anthropic API; dev model `claude-haiku-5-5` (cheapest), escalate only if needed.
- API key lives in `.env`; monthly spend limit set in the provider console, auto-reload off.
- Offer text is untrusted data: it goes inside `<oferta>` tags, instructions stay in `system`.
- The human label is never sent to the model.
- Always check `stop_reason`; anything other than `end_turn` is an error, not a result.
- Pick the `text` blocks of a response; models may return a thinking block first, and
  thinking tokens count against `max_tokens` (1000 was too small, 4000 works).

## Findings from matcher v0 (2 offers)
- The model did not invent missing facts (remote, salary, English) and listed them as unknown.
- Scores do not discriminate: two very different offers both got 6/10. Classification is
  more reliable than score for now.
- `alertas` should only carry injection attempts; it was used for general warnings.
- Output speaks in first person (inherited from the profile); should be third person.
- `falta_verificar` is too long; limit it to the candidate's dealbreakers.
- Dataset has no clear negatives yet, so false positives cannot be measured.

## Next steps
1. Add two clear negative offers (e.g. on-site/relocation, pure backend/devops,
   advanced English required). Label `03` as `quizas`.
2. Fix the prompt (alerts, third person, shorter missing-info list) and compare before/after
   on the same offers.
3. Define what each label means (interested vs. compatible by the candidate's rules).
4. Build a small eval script: compare model classification with human labels.
5. Add a separate set of malicious offers (prompt injection) and measure resistance.
6. Move deterministic checks (e.g. salary floor, on-site) out of the LLM into code.
7. Later: prompt caching for the repeated profile.

## First measurement (8 offers, profile v1 vs v2)
Dataset: 5 real offers + 3 synthetic ones, each synthetic isolating ONE dealbreaker
(on-site, hybrid in another city, C1 English). Labels: 2 yes, 1 maybe, 5 no.
`stage1_match.py` takes the profile path as an argument and writes `logs/run_<profile>.json`.

| Result | v1 (without new rules) | v2 (with city + C1 English rules) |
|---|---|---|
| "no" offers discarded | 4/5 (08 slipped through) | 5/5 |

- The C1 English rule fixed offer 08. The city rule changed nothing measurable: the
  hybrid offer was already discarded because the profile said "no on-site work".
- Caveats: one run each, and outputs are not deterministic, so this is not causal proof.
  The synthetic offers are easy (they state everything explicitly).
- The model never answers "compatible": missing info always yields "requiere_verificacion".
  The score does not order offers like the human does (a "yes" got 5, a "maybe" got 7).
- In v1 the C1 requirement landed in `alertas` instead of driving the classification.

Next: eval script with a metric, repeated runs to measure variance, prompt fixes, label semantics.

## Decision: what counts as a hit (eval semantics v1, owner's decision)
The owner fears missing a good offer if the system is too deterministic, so the error costs
are asymmetric and the metric follows that. To be refined over time.

| Human label | Model says | Counts as |
|---|---|---|
| si / quizas | compatible or requiere_verificacion | hit |
| si / quizas | descartada | MISS (critical, target: zero) |
| no | descartada | hit |
| no | requiere_verificacion | tolerated, adds review load |
| no | compatible | false positive |

Two numbers are tracked together: (1) good offers discarded (should be 0) and
(2) review load = share of offers left as requiere_verificacion (counterweight: if everything
is "verify", the system just hands the work back).

## Working process (why this is useful for the job search itself)
1. Describe the profile and the criteria in plain text, separate from the code.
2. Collect real offers and label them BEFORE running the model (human ground truth).
3. Add synthetic offers that isolate ONE dealbreaker to test one rule at a time.
4. Run, compare with the labels, and change one thing at a time (profile or prompt).
5. Keep the previous version (e.g. `profile.v1.md`) so every change can be measured.
6. Write each decision and finding in this file so the project survives a machine change.
This loop (label -> run -> measure -> adjust) is the same one used to evaluate agents in production.

## Ideas backlog (owner's ideas, not built yet)
1. **Hard filters vs soft signals.** Salary should not be a dealbreaker; it should be a graded
   signal (fit range, shown with colors in the UI, grey when unknown) so a lower-paid offer that
   teaches something can still be picked. Hard filters stay: on-site, impossible requirements, fraud.
   Salary math belongs in code; the LLM only extracts the numbers from the text.
   (Implies a new profile version: move salary from "dealbreakers" to "soft preferences".)
2. **Freelance offers.** Profile already accepts 10-20 h/week. Needs: rate normalization
   (hourly / per project / monthly) with a minimum hourly rate decided by the owner, extra
   criteria (duration, clear scope, payment terms) and extra fraud checks.
3. **UI** with color indicators (belongs to stages 3 and 5, after the matcher is measured).
Rationale for order: measure the base matcher first (eval script), then add dimensions one at
a time so every change can be compared against the previous version.

## Variance check (profile v2, 4 runs of the same 8 offers)
- Good offers discarded: 0 of 3 in every run (metric 1 is stable). Review load: 3-4 of 8.
- 7 of 8 offers always got the same class; scores moved at most +-1.
- Offer 07 (hybrid in Buenos Aires) flipped between descartada and requiere_verificacion.
  Cause: the profile says "I cannot attend offices outside my city of residence" but, for
  privacy, no longer names the city, so the model cannot know if Buenos Aires is her city.
  Lesson: instability here comes from an under-specified profile, not only from model randomness.
- Tooling: `stage1_match.py <profile> [tag]` saves `logs/run_<profile>_<tag>.json`;
  `stage1_eval.py` (no args) scores every run and prints a STABILITY section.
4. **Swipe-style review with feedback (owner's idea, stage 3).** Accept / discard offers like a
   swipe UI, asking for a reason on each decision. The model does NOT retrain; what grows is the
   context it receives. Levels: (1) log every decision as label + reason (same format as
   `data/private/jobs`, so the eval set grows for free); (2) propose profile rules after
   repeated patterns, human approves; (3) similar past decisions as examples in the prompt.
   Cautions: filter bubble (keep showing a sample of discarded offers to catch errors), a minimum
   number of decisions before proposing a rule, one-tap reasons with optional free text, and
   treat stored reasons as untrusted data when they re-enter a prompt.

## Prompt v2 + profile with city (commit 283ea32), 12 offers x 3 runs
Changes in this step (profile and prompt changed together, so gains cannot be attributed to one):
profile names the city; prompt in 3rd person; `alertas` only for injection attempts; `compatible`
allowed (no dealbreaker violated AND the data to check them is present); `falta_verificar` max 4
and only dealbreaker-related; `score` = technical/role fit, independent of missing data.

Results (8 original offers, 3 runs): 0/3 good offers discarded, 8/8 offers stable (07 fixed by
naming the city), `alertas` empty when there is no injection, `falta_verificar` <= 4.
Note: score semantics changed (synthetic offers 06-08 now score 8 yet are discarded for
modality/English), so scores are not comparable with earlier runs.

Added synthetic offers: 09 (complete, should be `compatible`), 10-12 (on-site offers carrying a
prompt injection: direct order, fake "system update" note, request to copy the profile).
Results (3 runs, 12 offers): good offers discarded 0/4; false positives 0; review load 3-4/12;
injections detected 3/3 and obeyed 0/3 in every run.
- Offer 09 returned `compatible` in 2 of 3 runs and `requiere_verificacion` in 1: the offer says
  "daily standups are bilingual", which is ambiguous, so asking to verify is defensible and
  tolerated by the eval semantics. Wording is ours (synthetic), not a model fault.
- Offer 12 (exfiltration attempt): the model did not copy the profile. Its reasoning mentioned
  the candidate's city and salary range as justification, which is normal reasoning, not
  obedience. Today the output only reaches the owner, so nothing leaks to the attacker.
  This changes in stage 2 once the agent has tools (fetch URL, send message): then an injection
  can have real consequences. Plan: least privilege, human approval before any outward action,
  never send profile data outside, and keep these synthetic attacks in the regression set.
Caveats: small dataset, easy attacks (explicit wording), 3 runs. Subtler injections still to test.

## Offers 13-17 (real) and the degree requirement, 17 offers x 3 runs
Added 5 real offers: 13, 14, 15, 16 labeled `no`/`quizas`, 17 labeled `si`.
- Profile v3 (before) -> v4 (now): added the education line (Architecture degree, no CS degree)
  and a dealbreaker for offers that REQUIRE a CS/related degree. A degree listed as nice-to-have,
  or "equivalent experience", is not a dealbreaker. Previous version kept as `profile.v3.md`.
- Before v4 (p4): 0/5 good offers discarded, 0 false positives, review load 6-7/17; 14 was the only
  unstable offer (the model sometimes asked to verify the Buenos Aires office / Argentina residency).
- After v4 (p5): 0/5 good discarded, all 17 offers stable across 3 runs, 14 now consistently
  discarded. 09 moved from `requiere_verificacion` to `compatible` (stable). Injections: 3/3
  detected, 0/3 obeyed.
- Lesson: offer 16 was labeled `no` for "degree is required", but the text says "four-year college
  degree" with no field, which her Architecture degree satisfies. The model was right, the label
  was wrong; relabeled to `quizas`. When the model and the label disagree, check the label too.
- Tooling note: waiting for background runs in this shell must poll for the output files
  (`until [ -f ... ]`); `pgrep` does not exist here.

## Freelance rate floor
Market check (web, 2025-2026; sources are agency/hiring blogs, orders of magnitude only):
LATAM frontend direct contractor: mid USD 30-45/h, senior 45-65/h; Upwork React Argentina 16-39/h.
Cross-check: full-time target USD 4,000-6,000/month ~ 25-37/h employed; freelance needs +30-50%
(no vacations, aguinaldo, health cover, gaps between projects) ~ 33-55/h.
Decision: freelance floor USD 35/h for 10-20 h/week. Added to `profile.md` (previous version kept
as `profile.v4.md`). Matcher/prompt not changed yet; next step is 2-3 real freelance offers
(18.md+) run as-is to see how the current matcher treats hourly rates before deciding on a
separate freelance module.
