# skills-public-release

Public-safe release bundle for two OpenClaw skills:

- `review-after-sales-closure`
- `zhanfu-browser`

## Included

- Skill folders only
- Publish-safe templates/examples for machine-specific references
- Minimal `.gitignore` to avoid committing caches and local runtime config

## Not included

- Local secrets
- Environment-specific exports
- Buyer-private data
- Runtime-generated outputs
- `local_config.json`

## Publish notes

Before using `zhanfu-browser` on a real machine:

1. Copy `scripts/local_config.sample.json` to `scripts/local_config.json`
2. Fill in machine-specific paths and store ids
3. Update `references/validated-state.md` and `references/store-map.md` for that machine
4. Keep those files public-safe if publishing again
