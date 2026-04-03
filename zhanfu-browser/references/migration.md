# Migration

## Goal
Move the ZhanFu collection skill to another OpenClaw environment with minimal manual changes.

## Recommended migration steps

1. Copy the entire `skills/zhanfu-browser` directory to the target OpenClaw workspace.
2. Ensure Python and required dependencies are available on the target Windows machine.
3. Run:

```powershell
python scripts\bootstrap_zhanfu_skill.py
```

4. Edit `scripts\local_config.json` for the target machine:
- `zhanfu_binary_path`
- `output_dir`
- `documents_dir`
- `fmcg_store_id`
- `default_store_ids`
- `default_input_csv`

5. Run:

```powershell
python scripts\self_test_zhanfu_skill.py
```

6. Run a healthcheck:

```powershell
python scripts\healthcheck_zhanfu.py --deep
```

7. Run a daily dry test or controlled manual run:

```powershell
python scripts\run_daily_collect.py --config scripts\collect_config.sample.json
```

## Notes

- The target machine should also have ZhanFu installed and logged in for the relevant stores.
- Store IDs may differ between environments; update `local_config.json` and collection config accordingly.
- Output paths should be writable by the OpenClaw runtime user.
- Prefer validating FMCG first before enabling a full scheduled run.
