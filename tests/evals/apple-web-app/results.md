# Behavioral review — 2026-09-05

Compared the original skill (version 2026-09-04.2) with the revised routing
and references using two separate GPT-5.6 Luna agents with inherited reasoning
effort. Both received the five inputs in cases.md and the skill under test;
neither received the rubric, suspected findings, or the other response. Each
agent handled its five cases in one batch, so this was a qualitative smoke
comparison, not five isolated trials or a GPT-6 benchmark.

| Case                   | Original                          | Revised                               | Observed difference                                                                             |
| :--------------------- | :-------------------------------- | :------------------------------------ | :---------------------------------------------------------------------------------------------- |
| Mac icon               | Correct focused 512/1024 PNG plan | Correct focused 512/1024 PNG plan     | Both avoided iOS assets                                                                         |
| Splash                 | Restored Apple capable tag        | Restored Apple capable tag            | Both separated rendered HTML checks and cold-launch verification                                |
| Safe area              | Base 56px plus inset              | Base 56px plus inset                  | Revised response explicitly preserved positioning/children and checked existing scroll behavior |
| Audit without hardware | Supplied conformity and unknowns  | Explicit Pass and Unverified outcomes | Revised response distinguished icon URL delivery from actual installed appearance               |
| Offline                | Skill excluded                    | Skill excluded                        | Both routed outside installed UI                                                                |

Both batches preserved the requested scope, proposed the expected fixes,
avoided blocking questions, and did not claim an actual device test. There was
no demonstrated correctness gain on these simple inputs. The observed benefit
was more explicit evidence reporting. No latency, cost or statistical reliability
measurement was performed.

Review of the first checklist draft caught overbroad checks: requiring a
particular scroll root, treating optional assets as mandatory, and grouping
static evidence with device appearance. The final checklist separates these.
A third fresh Luna agent ran the audit case against that final checklist. It
reported supplied evidence explicitly, separated icon delivery from installed
appearance and Back-button presence from route behavior, and excluded Mac/iPad.
It still listed unknown splash support as Unverified rather than deciding
whether the product includes startup images; that is an applicability unknown,
not a demonstrated missing-feature defect.

An independent review of the final changes found a pending-animation-frame
cleanup defect in the new overlay helper. It was fixed and covered by the
snippet tests before completion. Historical iOS baseline notes and navigation
findings were also restored during review.

The Node snippet tests execute JavaScript extracted from the Markdown examples.
They test visit idempotence and eligibility, dismissal/standalone exclusions,
overlay initialization, repeated-blur cancellation/cleanup, and the viewport
fallback on resize. They do not test browser layout or Safari behavior.
