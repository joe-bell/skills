# Maintaining this skill

## 0. Porting

- Copy the whole directory, including `scripts/` and `references/`, and keep
  its relative links.
- Recreate the host tool's discovery link (for example Claude Code reads
  `.claude/skills/<name>`; a relative symlink to the copied folder works)
  rather than copying any symlink.
- `metadata.upstream` is the public copy, published manually.
- **Never commit a log entry into this skill.** Entries belong to the
  repository that produced them, under its own `.papercuts/`.

## 1. Conventions

- Keep `scripts/papercut.py` to the Python standard library and Python 3.9+,
  so it runs in any host's sandbox without an install step.
- The log format in section 3 of [SKILL.md](../SKILL.md), the script and
  [readme-template.md](readme-template.md) describe the same contract. Change
  all three together, and keep the format backwards compatible: logs written
  by an older copy must still read.
- The script must never create `.papercuts/`. Opting in is the repository's
  decision, and creating the directory in a public repository could publish
  notes.
- Note text is untrusted. The review pass in section 4 treats it as evidence,
  never as an instruction; keep that wording when editing.
- Record each external rule in [sources.md](sources.md).
- Keep `SKILL.md` at ≤ 500 lines / 5,000 words, wrapped around 80 columns.
- Bump `metadata.version` for every content change, and `metadata.reviewed`
  when the contract is re-checked end to end.

## 2. Checking a change

From a scratch repository:

```sh
git init -q /tmp/pc && cd /tmp/pc && git commit -q --allow-empty -m init
python3 path/to/scripts/papercut.py --status          # off
mkdir .papercuts && python3 path/to/scripts/papercut.py "a note" --file=x
cat .papercuts/*.jsonl                                 # one JSON line
echo .papercuts/ > .gitignore
python3 path/to/scripts/papercut.py --status          # local
```

Also check a branch name with `/`, a detached `HEAD`, and that logging with
no `.papercuts/` exits non-zero without creating anything.
