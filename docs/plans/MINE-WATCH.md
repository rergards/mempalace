---
slug: MINE-WATCH
goal: "Add --watch flag to `mempalace mine` that uses OS-native file events to auto re-mine changed files"
risk: low
risk_note: "Self-contained new module; no changes to existing mine() logic; uses battle-tested watchfiles library (Rust-backed, already a transitive dep via uvicorn)"
files:
  - path: mempalace/watcher.py
    change: "New module — watch loop using watchfiles, debounce, signal handling, file filtering"
  - path: mempalace/cli.py
    change: "Add --watch flag to mine subcommand; dispatch to watcher when set"
  - path: pyproject.toml
    change: "Add [watch] optional dependency: watchfiles>=1.0"
  - path: tests/test_watcher.py
    change: "New test file — unit tests for debounce, filtering, graceful shutdown, incremental re-mine on change"
acceptance:
  - id: AC-1
    when: "User runs `mempalace mine <dir> --watch`"
    then: "Watcher starts, prints status line, and blocks (foreground daemon)"
  - id: AC-2
    when: "A source file in <dir> is modified or created while watcher is running"
    then: "Changed file is re-indexed within 10s (5s debounce + incremental mine)"
  - id: AC-3
    when: "Watcher is running and no files are changing"
    then: "CPU usage is near zero (watchfiles uses fsevents/inotify, no polling)"
  - id: AC-4
    when: "SIGTERM or SIGINT (Ctrl-C) is sent to the watcher process"
    then: "Watcher exits cleanly, flushes any pending batch, prints summary"
out_of_scope:
  - "Background daemon mode (launchd/systemd service) — foreground only for v1"
  - "Watch mode for --mode convos (conversation mining)"
  - "Watch mode for mine-all (multi-project)"
  - "Per-file surgical re-mine (reuses existing mine() with incremental=True)"
  - "Config file watching (mempalace.yaml changes)"
---

## Design Notes

### Library choice: `watchfiles` (not `watchdog`)

- `watchfiles` is Rust-backed (via `notify` crate), uses fsevents (macOS) and inotify (Linux) natively.
- Already a transitive dependency in the lock file (uvicorn pulls it in). Adding as explicit optional dep avoids relying on transitive availability.
- Simpler API than `watchdog`: `watchfiles.watch()` is a blocking iterator that yields sets of `(change_type, path)` tuples with built-in debounce.
- Pure sync API — no need for asyncio or threading.

### Architecture

```
cli.py --watch flag
  └── watcher.watch_and_mine(project_dir, palace_path, ...)
        ├── Load config, validate dir
        ├── Initial mine() call (incremental=True) — bring palace up to date
        ├── Register SIGTERM/SIGINT handler → sets shutdown flag
        └── watchfiles.watch(project_dir, ...) loop:
              ├── Filter changes through READABLE_EXTENSIONS + skip patterns
              ├── If any relevant changes remain → call mine(incremental=True)
              ├── mine() handles hash comparison, stale sweep, batching
              └── Check shutdown flag → break
```

### Key decisions

- **Reuse `mine()` wholesale** rather than extracting single-file re-mine. The incremental path in `mine()` already computes hashes for all files, skips unchanged ones in O(1), and only re-embeds changed files. For a watcher triggered by 1-3 file changes, the overhead is: one `scan_project()` walk + one `_bulk_existing_file_hashes()` query. Both are fast (<100ms for typical repos). This avoids duplicating complex logic (chunking, batching, KG extraction, stale sweep, optimize).

- **Debounce at 5000ms** via `watchfiles.watch(debounce=5000)`. This is the `watchfiles` built-in debounce — it waits until 5s of quiet before yielding the batch. Matches the task's "wait 5s after last change" requirement.

- **Filter before mining**: The watcher receives raw OS events including changes to `.git/`, `node_modules/`, `.pyc` files, etc. Before calling `mine()`, filter the change set through `READABLE_EXTENSIONS` and `should_skip_dir()` from `miner.py`. If no relevant files changed, skip the mine cycle entirely.

- **Foreground daemon**: `--watch` runs in the foreground (blocking). No daemonization for v1. User can background it with `&` or run in tmux/screen.

- **Signal handling**: Register `signal.signal(signal.SIGTERM, handler)` that sets an `threading.Event`. The `watchfiles.watch()` iterator is interrupted by the signal, and the loop checks the event to decide whether to exit. SIGINT (Ctrl-C) is handled naturally via `KeyboardInterrupt` (which `mine()` already catches).

- **Mutual exclusion with --dry-run**: `--watch` + `--dry-run` is rejected with an error — watching without writing is pointless.

- **Mutual exclusion with --full**: `--watch` always uses incremental mode. `--full` + `--watch` is rejected.

### CLI changes (cli.py)

Add to `p_mine` parser:
```python
p_mine.add_argument(
    "--watch",
    action="store_true",
    help="Watch for file changes and re-mine automatically (requires mempalace[watch])",
)
```

In `cmd_mine()`, when `args.watch` is set:
1. Validate: reject `--watch` with `--dry-run`, `--full`, or `--mode convos`.
2. Import `watcher.watch_and_mine()` with an ImportError guard that tells the user to install `mempalace[watch]`.
3. Delegate to `watch_and_mine()` with the same args that `mine()` would receive.

### Dependency (pyproject.toml)

```toml
watch = ["watchfiles>=1.0"]
```

Added as an optional extra, same pattern as `[chroma]`, `[spellcheck]`, `[treesitter]`.

### watcher.py module outline

```python
"""watcher.py — File watcher for auto-incremental mining."""

import signal
import sys
import threading
from pathlib import Path

def watch_and_mine(
    project_dir: str,
    palace_path: str,
    wing_override: str = None,
    agent: str = "mempalace",
    respect_gitignore: bool = True,
    include_ignored: list = None,
):
    """Watch project_dir for changes and re-mine incrementally."""
    # 1. Import watchfiles (fail with clear message if not installed)
    # 2. Initial incremental mine to bring palace up to date
    # 3. Set up shutdown event + signal handler
    # 4. Enter watchfiles.watch() loop with debounce=5000
    #    - Filter changes through _is_relevant_change()
    #    - Call mine(incremental=True) for relevant changes
    #    - Break on shutdown event
    # 5. Print summary on exit

def _is_relevant_change(path: str, project_path: Path) -> bool:
    """Return True if the changed path should trigger a re-mine."""
    # Check READABLE_EXTENSIONS, SKIP_FILENAMES, should_skip_dir()
```

### Test plan (tests/test_watcher.py)

- **test_watch_rejects_dry_run**: `--watch --dry-run` exits with error.
- **test_watch_rejects_full**: `--watch --full` exits with error.
- **test_watch_rejects_convos**: `--watch --mode convos` exits with error.
- **test_is_relevant_change_filters**: Unit test `_is_relevant_change()` with various paths (`.py` yes, `.pyc` no, `.git/` no, `node_modules/` no).
- **test_watch_detects_file_change**: Create a temp project, start watcher in a thread, modify a file, assert re-mine runs within timeout. Uses `threading.Timer` to stop watcher after assertion.
- **test_watch_handles_sigterm**: Start watcher in a subprocess, send SIGTERM, assert clean exit code 0.
- **test_import_error_message**: Mock `watchfiles` import failure, assert clear error message.
