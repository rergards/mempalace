---
slug: STORAGE-AUTO-BACKUP
goal: "Make pre-optimize auto-backup the default, add `backup list`, and add `backup schedule` snippet-emit for daily/weekly scheduling."
risk: medium
risk_note: "Changes a default that affects every mining run (backup_before_optimize False → True). The safe_optimize() fail-closed path is already hardened, so the worst-case failure mode is 'mine reports optimize skipped due to backup error' rather than silent data loss. Scheduled backup only emits a snippet — no system files are modified."
files:
  - path: mempalace/config.py
    change: "Flip DEFAULT_BACKUP_BEFORE_OPTIMIZE False → True. Add `auto_backup_before_optimize` property that reads MEMPALACE_AUTO_BACKUP_BEFORE_OPTIMIZE env or `auto_backup_before_optimize` file key, falling back to `backup_before_optimize` (back-compat). Add `backup_schedule` property (off|daily|weekly|hourly) reading MEMPALACE_BACKUP_SCHEDULE env / `backup_schedule` file key, default 'off'. The existing `backup_before_optimize` property remains the single source of truth consumed by miner.py / convo_miner.py — callers do not need to change."
  - path: mempalace/backup.py
    change: "Add `list_backups(palace_path, include_cwd=False) -> list[dict]`: scans <palace_parent>/backups/ for *.tar.gz, opens each tar to parse mempalace_backup/metadata.json (tolerate missing metadata), returns sorted-newest-first list of {path, size_bytes, mtime, timestamp, drawer_count, wings, kind}. `kind` is 'pre_optimize' for pre_optimize_*.tar.gz, 'manual' otherwise. Add `render_schedule(freq: str, mempalace_bin: str, platform: str) -> str`: returns launchd plist XML (platform='darwin') or cron line (platform='linux'); raises ValueError on unsupported freq/platform."
  - path: mempalace/cli.py
    change: "Refactor `backup` parser to a sub-subparser with verbs: `create` (existing behavior, default when no verb given for back-compat), `list`, `schedule`. `cmd_backup_list(args)` calls list_backups(); prints 'No backups found.' or a formatted table (timestamp, size, drawers, kind, path). `cmd_backup_schedule(args)` requires --freq {daily,weekly,hourly}; prints render_schedule() output. --install is explicitly rejected with an 'owner action required' message pointing at the emitted snippet. Dispatch `backup` to `cmd_backup` which branches on args.backup_command (None → create for back-compat)."
  - path: tests/test_backup.py
    change: "Add TestAutoBackupDefault (config flip, env override, file-key back-compat for backup_before_optimize=false, auto_backup_before_optimize alias override). Add TestListBackups (empty dir → []; seeded pre_optimize_*.tar.gz + mempalace_backup_*.tar.gz → both listed with correct kind; missing metadata.json tolerated; newest-first ordering). Add TestRenderSchedule (daily/weekly/hourly on darwin emits valid plist with StartCalendarInterval; linux emits cron line with correct minute/hour and the resolved binary path; invalid freq raises ValueError; invalid platform raises ValueError)."
  - path: tests/test_cli.py
    change: "Add test_backup_list_empty (no backups/ dir → stdout contains 'No backups found' exit 0), test_backup_list_populated (seeded palace with pre_optimize archive → stdout shows archive name and drawer count), test_backup_schedule_daily_darwin (monkeypatch sys.platform='darwin' → stdout contains 'plist' and 'StartCalendarInterval'), test_backup_schedule_daily_linux (monkeypatch sys.platform='linux' → stdout matches cron minute/hour pattern), test_backup_no_verb_creates (back-compat: `mempalace backup --out X` with no verb still creates archive), test_mine_default_calls_safe_optimize_backup_first (integration: mine() on a fresh MempalaceConfig() calls safe_optimize(backup_first=True) because of the flipped default)."
  - path: README.md
    change: "Update the 'Storage Safety' / 'backup_before_optimize' section to note auto-backup is ON by default, document the new `auto_backup_before_optimize` alias, and add a 'Scheduled backups' subsection pointing at `mempalace backup schedule --freq daily`."
acceptance:
  - id: AC-1
    when: "MempalaceConfig() is instantiated on a clean config dir (no config.json, no env vars)"
    then: "config.backup_before_optimize is True AND config.auto_backup_before_optimize is True AND config.backup_schedule == 'off'"
  - id: AC-2
    when: "MEMPALACE_BACKUP_BEFORE_OPTIMIZE=0 is set in the environment"
    then: "MempalaceConfig().backup_before_optimize is False (env opt-out overrides flipped default)"
  - id: AC-3
    when: "A user's config.json contains {\"backup_before_optimize\": false} (explicit opt-out from pre-flip era)"
    then: "MempalaceConfig().backup_before_optimize is False (file value honored; flipped default does not override explicit opt-out)"
  - id: AC-4
    when: "list_backups(palace_path) is called on a palace whose <palace_parent>/backups/ contains two pre_optimize_*.tar.gz archives seeded via create_backup()"
    then: "returns a length-2 list ordered newest-first; each entry has correct drawer_count from metadata.json and kind='pre_optimize'"
  - id: AC-5
    when: "`mempalace backup list` is run on a palace with no backups/ directory"
    then: "exit code 0; stdout contains 'No backups found.'"
  - id: AC-6
    when: "`mempalace backup --out /tmp/x.tar.gz` is run (no verb, back-compat path)"
    then: "exit code 0; /tmp/x.tar.gz exists and is a valid backup archive"
  - id: AC-7
    when: "`mempalace backup schedule --freq daily` is run with sys.platform='darwin'"
    then: "exit code 0; stdout contains '<?xml' and 'StartCalendarInterval' and the mempalace binary path"
  - id: AC-8
    when: "`mempalace backup schedule --freq daily` is run with sys.platform='linux'"
    then: "exit code 0; stdout contains a line matching `^\\d+\\s+\\d+\\s+\\*\\s+\\*\\s+\\*\\s+.*mempalace.*backup$`"
  - id: AC-9
    when: "miner.mine() is invoked with default MempalaceConfig() (no overrides) on a LanceDB palace"
    then: "the store's safe_optimize is called with backup_first=True (verified via mock)"
  - id: AC-10
    when: "`ruff check mempalace/ tests/` and `ruff format --check mempalace/ tests/` are run"
    then: "both exit 0; `python -m pytest tests/ -x -q` still passes (no regressions in the 570+ existing tests)"
out_of_scope:
  - "Retention/pruning of old backup archives — tracked as STORAGE-BACKUP-RETENTION (separate open backlog item that explicitly handles pre_optimize_*.tar.gz cleanup)."
  - "Actually installing launchd plists or writing crontab entries — the subcommand only emits the snippet; the user is responsible for installation (owner_prereq)."
  - "Incremental / differential backups using Lance table versioning — full-tar backup is fast enough for realistic palace sizes (< 500 MB typical). Post-v1 optimization; would need its own design + benchmark."
  - "ChromaStore backup — ChromaDB is deprecated; backup.py already targets LanceDB only."
  - "Migrating existing users' config.json to add auto_backup_before_optimize key — alias is read-only; users who explicitly set backup_before_optimize=false keep their setting (AC-3)."
  - "Changing the pre_optimize_*.tar.gz file naming / directory layout — safe_optimize() already standardized it."
  - "A `mempalace backup restore <name>` shorthand that looks up archives by name in the backups/ dir — the existing `mempalace restore <path>` already works."
  - "A `backup verify` subcommand that opens the archive and validates contents — out of scope; would need a separate plan."
---

## Design Notes

- **Why flip the default.** The backlog incident summary ("Lost 39 drawers in Apr 2026") points at the same root cause as STORAGE-SAFE-OPTIMIZE: the safety machinery exists but is off. Flipping the default is the single largest safety win here. Explicit opt-out is still honored (AC-2 env, AC-3 file).

- **Why the alias, not a rename.** Renaming `backup_before_optimize` → `auto_backup_before_optimize` would break every existing config.json and every env-var override in user setups. Instead: `auto_backup_before_optimize` is a preferred alias that reads first; `backup_before_optimize` remains the canonical key consumed by miner.py / convo_miner.py. No caller in the code base needs to change.

- **Where backups go.** `safe_optimize()` already writes to `<palace_parent>/backups/pre_optimize_<ts>.tar.gz`. `list_backups()` reads from that directory plus any manual `mempalace_backup_*.tar.gz` siblings. The `include_cwd` knob is deliberately off-by-default — scanning CWD is surprising behavior for a per-palace command.

- **List parsing tolerance.** Corrupted/partial archives should not crash `backup list`. Each tar open is wrapped in a try/except; a missing or unparseable `metadata.json` yields `drawer_count=None, wings=[]` but the entry still appears (with mtime/size from filesystem). This matches the failure mode of the very incident that motivated the feature.

- **Schedule command emits, does not install.** Writing a launchd plist or editing crontab is a destructive system-level action. Per CLAUDE.md "Ask Before Acting" and the executing-actions-with-care rule, the subcommand prints the snippet and tells the user to install it (owner_prereq). The acceptance tests are platform-patched so they run deterministically in CI.

- **Schedule content.** launchd plist uses `StartCalendarInterval` with `Hour=3, Minute=0` for daily (so backup runs during low-activity hours). Weekly uses `Weekday=0` (Sunday 03:00). Hourly uses `StartInterval=3600`. Cron equivalent: `0 3 * * *` / `0 3 * * 0` / `0 * * * *`. The resolved binary path comes from `shutil.which('mempalace')` with a fallback to `sys.executable + ' -m mempalace'` when not on PATH.

- **`backup list` output shape.** Columns: `TIMESTAMP  SIZE  DRAWERS  KIND  PATH`. Fixed-width columns (not JSON) — matches the existing CLI aesthetic in `status` / `diary read`. JSON output is explicitly not in this plan's scope; add later if an agent needs it.

- **Back-compat verb dispatch.** `p_backup.add_subparsers(dest="backup_command")` with `required=False` lets `mempalace backup --out X` keep working (args.backup_command=None → dispatch to create path). This mirrors the existing `diary` pattern but relaxes the required=True gate `diary` uses, because `backup` already had a working no-verb form pre-this-plan.

- **Why `auto_backup_before_optimize` has MEMPALACE_AUTO_BACKUP_BEFORE_OPTIMIZE env.** Consistency: the backlog AC specifies the file key name, and env-var naming follows the `MEMPALACE_<UPPER_SNAKE>` convention used throughout config.py. Both env vars work; the auto_ variant is read first if set.
