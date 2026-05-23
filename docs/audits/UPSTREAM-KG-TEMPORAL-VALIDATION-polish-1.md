slug: UPSTREAM-KG-TEMPORAL-VALIDATION
phase: polish
date: 2026-05-23
commit_range: 3141917..HEAD
reverted: false
findings:
  - id: P-1
    title: "Impossible asserts used as type narrowers in _validate_window"
    category: defensive
    location: "mempalace_code/knowledge_graph.py:106-107"
    evidence: |
      assert cmp_vf is not None
      assert cmp_vt is not None
      Both follow _as_comparable(vf) / _as_comparable(vt) immediately after the
      'if vf is None or vt is None: return' guard, so neither can ever be None at
      that point. Runtime asserts that cannot fire are defensive slop.
    decision: fixed
    fix: >
      Replaced the two asserts with a single conditional guard on the comparison:
      'if cmp_vf is not None and cmp_vt is not None and cmp_vt < cmp_vf:'.
      Satisfies Pyright without runtime assertions that cannot fail.

  - id: P-2
    title: "Impossible assert used as type narrower in _in_window"
    category: defensive
    location: "mempalace_code/knowledge_graph.py:121"
    evidence: |
      cmp = _as_comparable(as_of)
      assert cmp is not None
      as_of is typed 'date | datetime' (not None), so _as_comparable always returns
      a datetime here. The assert can never fire.
    decision: fixed
    fix: >
      Replaced with 'if cmp is None: return True' — an early-return guard that
      narrows the type for Pyright without a runtime assertion. Behavior is
      identical since the branch is unreachable.

  - id: P-3
    title: "Inline comments restating that _parse_temporal raises ValueError"
    category: verbal
    location: "mempalace_code/knowledge_graph.py:284,312,351,399,417,457,510"
    evidence: |
      _parse_temporal(ended)  # raises ValueError for invalid temporal strings
      _parse_temporal(ended_str)  # raises ValueError if invalid
      as_of_parsed = _parse_temporal(as_of)  # raises ValueError for invalid inputs
      Seven occurrences. The docstring already documents the ValueError contract;
      the call site comments add no information that a reader cannot get from the
      function name and its docstring.
    decision: fixed
    fix: "Removed all seven inline # raises ValueError... comments."

totals:
  fixed: 3
  dismissed: 0
fixes_applied:
  - "Replaced impossible asserts in _validate_window with a single None-guarded comparison"
  - "Replaced impossible assert in _in_window with an early-return None guard"
  - "Removed seven inline comments restating _parse_temporal ValueError contract"
