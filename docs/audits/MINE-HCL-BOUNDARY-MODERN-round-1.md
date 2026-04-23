slug: MINE-HCL-BOUNDARY-MODERN
round: 1
date: 2026-04-24
commit_range: cd9582f..cd9582f
findings:
  - id: F-1
    title: "tfvars assignment guard backtracked across repeated whitespace"
    severity: medium
    location: "mempalace/miner.py:699"
    claim: >
      The HCL_BOUNDARY guard used \s+(?!=), which rejects `moved = "x"` but can
      backtrack and accept `moved    = "x"` because the lookahead sees whitespace
      instead of `=`. That would turn tfvars assignments using modern Terraform
      block keywords into false structural boundaries.
    decision: fixed
    fix: >
      Changed the regex to look ahead from the keyword for whitespace followed by
      a non-whitespace, non-equals character, and extended the tfvars regression
      test to include spaces and tabs before `=`.
totals:
  fixed: 1
  backlogged: 0
  dismissed: 0
fixes_applied:
  - "Tightened HCL_BOUNDARY's post-keyword lookahead to reject assignments with repeated spaces or tabs before equals."
  - "Extended the tfvars fallback test with repeated-space and tabbed assignments for import, check, and removed keys."
new_backlog: []
