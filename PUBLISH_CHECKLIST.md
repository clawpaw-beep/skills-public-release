# Publish Checklist

Before pushing any change to this public repository, run through every item.

---

## ☐ Sensitive Content Scan

### Hardcoded secrets — ZERO TOLERANCE
- [ ] No `secrets`, `token`, `api_key`, `APP_SECRET`, `private_key` in any file
- [ ] No `.env`, `local_config.json`, `credentials.json`, `cookies.json`
- [ ] No real phone numbers, buyer addresses, buyer emails in any export or log
- [ ] No real order IDs that can be traced back to real buyers
- [ ] No Twilio auth tokens or API keys
- [ ] No machine-specific user paths that identify a person (e.g. `C:\Users\<name>\...`)

### Placeholder / template files only
- [ ] `local_config.sample.json` — only placeholder values, no real credentials
- [ ] `collect_config.sample.json` — only example store IDs, no live production IDs
- [ ] `validated-state.md` — only generic paths and public-safe examples
- [ ] `store-map.md` — only example store IDs, no real store data

### Git-tracked files
- [ ] `git status` shows only intended changes
- [ ] No `local_config.json` accidentally committed
- [ ] No `runs_index.json`, `daily_run_*` output folders committed
- [ ] No `__pycache__/`, `*.pyc`, `*.log` committed

---

## ☐ Skill Completeness Check

### zhanfu-browser
- [ ] `SKILL.md` — description is clear, Windows runtime assumptions are explicit
- [ ] `references/migration.md` — migration steps are accurate
- [ ] `references/collector-spec.md` — collector spec is up to date
- [ ] `scripts/local_config.sample.json` — all keys documented
- [ ] `scripts/bootstrap_zhanfu_skill.py` — still works on fresh Windows install
- [ ] No broken script references (all scripts listed in SKILL.md exist)

### review-after-sales-closure
- [ ] `SKILL.md` — works without hardcoded Windows paths
- [ ] `references/architecture.md` — architecture is current
- [ ] `references/csv-schema.md` — schema fields are documented
- [ ] No Twilio credentials anywhere in the repo

---

## ☐ Documentation Quality

- [ ] README.md reflects current repo structure
- [ ] README.md has clear "How to Install" section for each skill
- [ ] README.md has clear "What is NOT included" section
- [ ] Any new skill folder has its own `SKILL.md`

---

## ☐ Pre-commit verification commands

```bash
# Must return empty — zero matches
grep -r "api_key\|apiSecret\|APPSECRET\|token\|password\|secret" --include="*.py" --include="*.json" --include="*.md" .
grep -r "C:\\Users\\" --include="*.py" --include="*.json" --include="*.md" .
grep -r "0.0.0.0\|127.0.0.1\|localhost" --include="*.py" --include="*.json" . | grep -v "sample\|template\|example"

# Must show only intended files
git status

# Must not show these file patterns
git status --porcelain | grep -E "local_config.json|runs_index.json|daily_run_|__pycache__|\.pyc|\.log$"
```

---

## ☐ After Push

- [ ] GitHub Actions / CI passes (if any)
- [ ] Test install on a clean machine:
  ```bash
  npx skills add https://github.com/clawpaw-beep/skills-public-release --dir zhanfu-browser
  npx skills add https://github.com/clawpaw-beep/skills-public-release --dir review-after-sales-closure
  ```
- [ ] Update this checklist if new risk patterns are discovered
