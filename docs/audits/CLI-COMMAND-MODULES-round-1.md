slug: CLI-COMMAND-MODULES
round: 1
date: 2026-05-12
commit_range: 9fc8783..d4f5fd4
findings:
  - id: F-1
    title: "resolve_palace helper in common.py is dead code — never called"
    severity: low
    location: "mempalace_code/cli_commands/common.py:6"
    claim: >
      resolve_palace() was added to common.py as a shared palace-path helper,
      but every command module inlines `os.path.expanduser(args.palace) if
      args.palace else MempalaceConfig().palace_path` directly. The function
      is defined but never imported or called anywhere. It also dragged in an
      otherwise-unused `import os` at module level.
    decision: fixed
    fix: >
      Removed resolve_palace() and the now-unused `import os` from common.py.
      All command modules already inline the resolution correctly.

  - id: F-2
    title: "Test module docstring claims dispatch coverage but no test existed"
    severity: low
    location: "tests/test_cli_command_modules.py:1"
    claim: >
      The module docstring listed "The dispatch mapping covers all expected
      command names" as a verification goal, but no test in the file checked
      that the dispatch dict in cli.main() (or the handler mapping from command
      name to callable) was complete. A missing or misnamed handler would cause
      a KeyError at dispatch time without any test catching the regression.
    decision: fixed
    fix: >
      Corrected the docstring to accurately describe what is tested.
      Added test_dispatch_keys_cover_all_expected_commands() which verifies
      that each of the 21 expected subcommand names maps to a callable handler
      in its owning module (ingest, query, maintenance, watch, backup_restore,
      diary, export_import, model, alias). This covers the handler-ownership
      contract and catches accidental renames or removals.

  - id: F-3
    title: "cmd_export and cmd_import skip os.path.expanduser for --palace"
    severity: medium
    location: "mempalace_code/cli_commands/export_import.py:11"
    claim: >
      Both cmd_export and cmd_import use `args.palace or
      MempalaceConfig().palace_path` without calling os.path.expanduser, so
      a user passing `--palace ~/custom/palace` would get a path with a
      literal `~` instead of the expanded home directory. All other command
      modules correctly call os.path.expanduser(). However, inspection of the
      pre-refactor cli.py (commit 9fc8783) confirms this is identical to the
      original code — it is a pre-existing bug faithfully preserved, not a
      regression introduced by this task.
    decision: dismissed
    fix: ~

  - id: F-4
    title: "test_no_eager_heavy_imports_on_cli_import is a no-op in full-suite runs"
    severity: info
    location: "tests/test_cli_command_modules.py:44"
    claim: >
      The test snapshots sys.modules before and after `import mempalace_code.cli`
      to detect eagerly-loaded heavy deps. When run as part of the full test
      suite, mempalace_code.cli is already in sys.modules so the re-import is a
      no-op and nothing new is added. The test comment acknowledges this
      ("most useful when run in isolation"). In practice, the implementation
      is correct by construction (all heavy imports are function-local) and the
      test provides no additional regression protection in the suite context.
      No action is required.
    decision: dismissed
    fix: ~

totals:
  fixed: 2
  backlogged: 0
  dismissed: 2

fixes_applied:
  - "Removed dead resolve_palace() helper and unused import os from common.py"
  - "Added test_dispatch_keys_cover_all_expected_commands() to test_cli_command_modules.py and corrected module docstring"

new_backlog: []
