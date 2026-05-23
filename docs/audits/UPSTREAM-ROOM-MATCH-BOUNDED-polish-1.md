slug: UPSTREAM-ROOM-MATCH-BOUNDED
phase: polish
date: 2026-05-23
commit_range: 4a600b9..HEAD
reverted: false
findings:
  - id: P-1
    title: "Redundant negative assertions in regression tests"
    category: defensive
    location: "tests/test_miner.py:3126,3137,3162"
    evidence: |
      assert result == "research"
      assert result != "frontend"  # appears in three tests after the positive assertion
    decision: fixed
    fix: "Removed the three `assert result != \"frontend\"` lines; the positive assertion already proves the result cannot be \"frontend\"."

  - id: P-2
    title: "Empty-guard in _tokens_match is redundant with _token_seq_in's n==0 guard"
    category: defensive
    location: "mempalace_code/mining/projects.py:73-74"
    evidence: "_token_seq_in already returns False when n==0, so passing [] to it is safe. The guard in _tokens_match is an early exit, not a correctness requirement."
    decision: dismissed
    reason: "The guard makes the function self-contained and documents intent for empty token sequences; removing it saves one line at the cost of clarity."

  - id: P-3
    title: "not text_tokens in _count_keyword_occurrences is redundant"
    category: defensive
    location: "mempalace_code/mining/projects.py:80"
    evidence: "When text_tokens is empty and kw_tokens is non-empty, h-n < 0 and the while loop never executes. The `not kw_tokens` guard is load-bearing (prevents infinite loop when n==0); `not text_tokens` is not."
    decision: dismissed
    reason: "Combined guard reads naturally as 'either empty = return 0'; the redundant half is harmless and bundles with the necessary half cleanly."

totals:
  fixed: 1
  dismissed: 2
fixes_applied:
  - "Removed three redundant `assert result != 'frontend'` assertions from TestDetectRoomBoundedMatching tests"
