slug: UPSTREAM-SEARCH-READ-SLICES
phase: polish
date: 2026-05-24
commit_range: c18cfd2..HEAD
reverted: false
findings:
  - id: P-1
    title: "Task slug baked into storage.py field comment"
    category: verbal
    location: "mempalace_code/storage.py:265"
    evidence: "# Line range metadata (UPSTREAM-SEARCH-READ-SLICES)"
    decision: fixed
    fix: "Collapsed two comment lines into one, removing the task slug: '# Line range metadata; 0 means unknown (legacy rows or chunks without exact-match).'"

  - id: P-2
    title: "Defensive getattr fallback on argparse-guaranteed attribute"
    category: defensive
    location: "mempalace_code/cli_commands/query.py:172"
    evidence: "wing=getattr(args, 'wing', None) — args always comes from the read subparser which adds --wing default=None"
    decision: fixed
    fix: "Changed to wing=args.wing; the attribute is always present via argparse."

  - id: P-3
    title: "Underscore prefix on actively-used local variables"
    category: volume
    location: "mempalace_code/mining/orchestrator.py:177,184"
    evidence: "_line_offset = leading.count(...) and _cursor = 0 — both are actively read in the loop body"
    decision: dismissed
    reason: "Borderline style preference; the names are local to the function and correct. Renaming risks test churn without clear slop benefit."

totals:
  fixed: 2
  dismissed: 1
fixes_applied:
  - "Removed UPSTREAM-SEARCH-READ-SLICES task slug from storage.py field comment"
  - "Replaced getattr(args, 'wing', None) with args.wing in cmd_read"
