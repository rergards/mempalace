slug: ARCH-RETRIEVAL
round: 1
date: "2026-04-18"
commit_range: adb02c1..b61af0e
findings:
  - id: F-1
    title: "n_results not clamped before use — negative values produce wrong Python slice behavior"
    severity: low
    location: "mempalace/mcp_server.py:535,545"
    claim: >
      tool_explain_subsystem passes n_results * 2 to code_search() and uses
      entry_points[:n_results] to trim the result list without validating the value first.
      code_search() in searcher.py clamps its own n_results via max(1, min(50, n)) before
      any use (searcher.py:255), but tool_explain_subsystem has no equivalent guard.
      For n_results=0, entry_points[:0] silently returns an empty list with no error.
      For n_results=-1, Python slice semantics evaluate entry_points[:-1] — removing the
      last element instead of limiting the count — producing wrong output with no diagnostic.
      No crash occurs, but callers receive incorrect results for out-of-range inputs.
    decision: backlogged
    backlog_slug: EXPLAIN-NRESULTS-CLAMP

  - id: F-2
    title: "Over-fetch n_results*2 loses effectiveness at n_results > 25 due to code_search's 50-cap"
    severity: info
    location: "mempalace/mcp_server.py:535"
    claim: >
      code_search() clamps its n_results to max(1, min(50, n)). When tool_explain_subsystem
      calls code_search(n_results=n_results*2), the 2x over-fetch benefit is reduced for
      n_results > 25 and eliminated entirely at n_results=50 (requests 100, receives 50).
      In a mixed palace with many prose drawers and a large n_results, the post-filter step
      may return fewer code-shaped entry_points than the caller expects. The plan's over-fetch
      note documents the *2 heuristic but does not call out this cap interaction.
    decision: dismissed

totals:
  fixed: 0
  backlogged: 1
  dismissed: 1

fixes_applied: []

new_backlog:
  - slug: EXPLAIN-NRESULTS-CLAMP
    summary: "Clamp n_results in tool_explain_subsystem and add boundary tests for 0 and negative values"
