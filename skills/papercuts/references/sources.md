# Sources & credits

Format: **Author — Title (date) — URL** — what this skill took from it.

## Background

- **Anthropic — How AI is transforming work at Anthropic (2025) —
  https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic**
  — the term and the case for it: about 8.6% of the Claude Code tasks studied
  were "papercut" fixes, small quality-of-life improvements that would
  otherwise never be prioritised. The article describes no capture process;
  the log in this skill is not from it.
- **Anthropic — Best practices for Claude Code (checked 2026-10-13) —
  https://code.claude.com/docs/en/best-practices** — keep always-loaded
  instructions short, add a rule only after a repeated mistake, and prefer a
  deterministic mechanism over an instruction. Section 4's "prefer a
  mechanical fix" and "one line" rules come from here.
- **Anthropic — Extend Claude with skills (checked 2026-10-13) —
  https://code.claude.com/docs/en/skills** — a skill loads when its
  description matches the request, which is why section 5 adds an
  always-loaded pointer to the repository's agent instructions.

## Prior art

- **Trey Goff — papercuts (checked 2026-10-13) —
  https://github.com/treygoff24/papercuts** — an append-only JSONL log at the
  repository root that agents write one line to mid-task, committed by
  default. The one-line, keep-going logging contract.
- **TheMikeFactoryMustGrow — papercuts (checked 2026-10-13) —
  https://github.com/TheMikeFactoryMustGrow/papercuts** — the "sand" pass that
  fixes entries by shared cause rather than one by one (section 4, step 3),
  and keeping logging opt-in per project rather than global (section 1).
- **every-app — open-seo `papercuts` skill (checked 2026-10-13) —
  https://github.com/every-app/open-seo** — log only friction that genuinely
  cost something, not every hiccup (the bar in section 2).

## Design choices not taken from a source

- One log file per branch, so parallel worktrees and pull requests never
  conflict on the same file.
- Opt-in by the presence of `.papercuts/`, with a gitignored directory for
  repositories whose history is public.
- Clearing ingested entries in the same change that carries their fixes.
