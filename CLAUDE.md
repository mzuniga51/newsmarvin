# Newsmarvin - Claude Code notes

For operational details, read `PLAYBOOK.md` in this directory before making changes. It is the source of truth; the README has known inaccuracies.

## Load-bearing rules

1. **Repo is owned by GitHub account `mzuniga51`, not `miabogadoai`.** Before any `git push` or `gh` command against `mzuniga51/newsmarvin`, run `gh auth switch -u mzuniga51` - the default session is usually the other account and will 403.

2. **Cloudflare Pages is NOT git-linked.** Pushing to `main` does not deploy. The live site only updates when `npx wrangler pages deploy output/ --project-name=newsmarvin --branch=main` runs (either locally or via the GitHub Actions workflows in `.github/workflows/`).

3. **The Marvin logo must never be removed.** Marvin was Manuel's Pomeranian who passed away in March 2026. The project is a tribute. If there's a performance problem involving the logo, optimize it (compression, WebP, lazy-load) - do not remove or hide it.

4. **`output/` is gitignored.** Regenerate it with `python3 aggregate.py` before any deploy. Git push alone ships nothing to the live site.

## Style

- Voice and writing rules: see `~/.claude/about-me/` (`writing-rules.md` in particular). Em-dash ban and diacritics rules are enforced there, not duplicated here.
- All display times are Costa Rica CST (UTC-6). `TIMEZONE_OFFSET = -6` in `config.py`.

Everything else - environment variables, deploy sequence, troubleshooting, architecture, file map - is in `PLAYBOOK.md`.
