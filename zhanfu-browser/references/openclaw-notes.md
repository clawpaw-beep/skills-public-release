# OpenClaw Notes Verified on 2026-04-02

## Current local OpenClaw state

- Main config: `C:\Users\9400\.openclaw\openclaw.json`
- Gateway health endpoint: `http://127.0.0.1:18789/health`
- Gateway mode: local
- Local node status: paired and connected
- Model context window for the current MiniMax model: `1048576` (`1M`)

## Fixes already applied

- `openclaw.json` was updated so the MiniMax model now uses `contextWindow: 1048576`.
- `C:\Users\9400\openclaw_auto.ps1` and `C:\Users\9400\openclaw_start.bat` were aligned with the current gateway token.
- The local node was re-paired so `openclaw node run` no longer fails with `pairing required`.
- The ZhanFu launch entry points in `C:\Users\9400\.openclaw\workspace` now prefer the portable runtime at `C:\Users\9400\ZhanFu_5_2_88_portable\站斧.exe`.

## Practical checks

- If the gateway is healthy but no node is connected, inspect node pairing before debugging the skill itself.
- If `openclaw node run` fails with `pairing required`, approve the pending local device/node pairing using the existing local gateway credentials from `openclaw.json`. Do not invent or hardcode a new token.
- If the user reports "OpenClaw can talk but automation cannot execute", verify both:
  - OpenClaw gateway/node connectivity
  - ZhanFu WebDriver availability on `127.0.0.1:45008`
  - The listening `45008` process path. On this machine it should point to `C:\Users\9400\ZhanFu_5_2_88_portable\站斧.exe`.

## Boundary

- Use OpenClaw to orchestrate the work.
- Use ZhanFu and Playwright/CDP to operate the store browsers.
- Keep buyer-private contact details out of exported files even when the store owner asks for batch statistics.
