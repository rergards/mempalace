slug: CLI-COMMAND-MODULES
phase: polish
date: 2026-05-12
commit_range: 9fc8783..538c5d3
reverted: false
findings:
  - id: P-1
    title: "Redundant `import sys as _sys` inside cmd_backup_schedule"
    category: volume
    location: "mempalace_code/cli_commands/backup_restore.py:79"
    evidence: "`import sys as _sys` followed by `_sys.platform` while `sys` is already a module-level import (line 3) and `sys.stderr` is used in the same function"
    decision: fixed
    fix: "Removed inner import; replaced `_sys.platform` with `sys.platform`"

  - id: P-2
    title: "Redundant `import sys as _sys` inside cmd_watch_schedule"
    category: volume
    location: "mempalace_code/cli_commands/watch.py:37"
    evidence: "`import sys as _sys` at function start; `_sys.platform` used alongside `sys.stderr` — inconsistent aliases when `sys` is already module-level (line 4)"
    decision: fixed
    fix: "Removed inner import; replaced `_sys.platform` with `sys.platform`"

  - id: P-3
    title: "Redundant `import sys as _sys` inside cmd_split"
    category: volume
    location: "mempalace_code/cli_commands/ingest.py:319"
    evidence: "`import sys as _sys` to alias `_sys.argv` manipulation, while `sys` is already imported at module level (line 4)"
    decision: fixed
    fix: "Removed inner import; replaced `_sys.argv` with `sys.argv`"

totals:
  fixed: 3
  dismissed: 0
fixes_applied:
  - "Removed redundant `import sys as _sys` in cmd_backup_schedule; use module-level sys.platform"
  - "Removed redundant `import sys as _sys` in cmd_watch_schedule; use module-level sys.platform"
  - "Removed redundant `import sys as _sys` in cmd_split; use module-level sys.argv"
