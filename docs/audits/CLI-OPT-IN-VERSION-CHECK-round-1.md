slug: CLI-OPT-IN-VERSION-CHECK
round: 1
date: 2026-05-12
commit_range: d679934..HEAD
findings:
  - id: F-1
    title: "--status flag not registered in version-check parser"
    severity: high
    location: "mempalace_code/cli.py:567-583"
    claim: >
      The version-check subparser defines a mutually exclusive group with --enable,
      --disable, and --check-now, but omits --status. Running
      `mempalace-code version-check --status` raises an argparse error
      ("unrecognized arguments: --status") with exit code 2, despite the
      --enable handler advertising the flag and the plan contract (REQ-3 / AC-3)
      requiring it. The CLI integration test named for --status invoked bare
      `version-check` instead, so the regression was not caught at verify time.
    decision: fixed
    fix: >
      Added `--status` to the mutually exclusive group in cli.py. Updated
      test_version_check_subcommand_status in tests/test_cli.py to invoke both
      bare `version-check` (default) and `version-check --status` explicitly,
      asserting both produce status output.
totals:
  fixed: 1
  backlogged: 0
  dismissed: 0
fixes_applied:
  - "Add --status to version-check mutually exclusive group in cli.py; update CLI test to exercise both bare and --status forms"
new_backlog: []
