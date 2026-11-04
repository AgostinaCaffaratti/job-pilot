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
