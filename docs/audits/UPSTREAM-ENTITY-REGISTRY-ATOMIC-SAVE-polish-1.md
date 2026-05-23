slug: UPSTREAM-ENTITY-REGISTRY-ATOMIC-SAVE
phase: polish
date: 2026-05-23
commit_range: 06e38eb..7d0e595
reverted: false
findings:
  - id: P-1
    title: "Impossible hasattr(os, 'stat') guard in permission skip condition"
    category: defensive
    location: "tests/test_entity_registry.py:105"
    evidence: "if platform.system() == \"Windows\" or not hasattr(os, \"stat\"):"
    decision: fixed
    fix: "Removed 'or not hasattr(os, \"stat\")' — os.stat is always present under CPython 3.11+ on any supported platform; the Windows branch is the only meaningful guard."
totals:
  fixed: 1
  dismissed: 0
fixes_applied:
  - "Remove dead 'not hasattr(os, \"stat\")' clause from platform skip condition in test_save_sets_restrictive_permissions_where_supported"
