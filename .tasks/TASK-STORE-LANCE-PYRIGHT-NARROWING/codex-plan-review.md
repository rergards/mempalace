verdict: NEEDS_CHANGES

gaps:
  - severity: high
    claim: "The task goal is pyright-cleanliness, but no acceptance criterion gates on pyright output. All five ACs are behavioral pytest commands; the only mention of pyright is in Design Notes ('Expected result: 0 errors'), which is not enforceable as an AC. An implementation could pass every listed pytest invocation while still emitting all 26 current reportOptionalMemberAccess / reportAttributeAccessIssue errors, defeating the task's stated purpose ('Make LanceStore optional handles Pyright-clean')."
    evidence: "docs/plans/STORE-LANCE-PYRIGHT-NARROWING.md acceptance: block (lines 9–24) — only behavioral tests; line 53 mentions pyright only in Design Notes."
    suggested_fix: "Add an AC such as: 'when: `python -m pyright mempalace_code/storage.py --pythonpath \"$(python -c 'import sys; print(sys.executable)')\"` is run; then: 0 errors are reported for `mempalace_code/storage.py`'. This is the primary observable success criterion for this task and must gate implementation."
  - severity: medium
    claim: "Plan calls out `_require_db()` only for `_open_or_create`, but `_db.open_table` is also used in `recover_to_last_working_version` (storage.py:1147) on the non-dry-run path. Pyright currently flags this line (reportOptionalMemberAccess at 1147:32). Without an explicit instruction, implementer may miss this site and leave one residual pyright error."
    evidence: "mempalace_code/storage.py:1147 `self._table = self._db.open_table(_LANCE_TABLE)`; pyright output line 1147:32; plan Design Notes line 49 (only mentions `_open_or_create`)."
    suggested_fix: "Generalize the design note to: 'Apply `_require_db()` at every non-read-only `self._db` access site, including `recover_to_last_working_version`'s post-restore reopen.' Or add a corresponding AC test for non-dry-run recovery."
  - severity: low
    claim: "Plan does not mention that `LanceStore._table` and `LanceStore._db` are accessed externally from `mempalace_code/mcp_server.py:88-89` via `is None` checks. These are safe with the proposed Optional[Protocol] typing, but the plan's `files:` list omits any acknowledgment of cross-module impact. Worth a sentence so reviewers don't worry about it."
    evidence: "mempalace_code/mcp_server.py:88 `if isinstance(new_store, LanceStore) and new_store._table is None:` and :89 `if new_store._db is None:`."
    suggested_fix: "Add a one-line note to Design Notes confirming external `is None` access in mcp_server.py remains compatible with the new Optional[Protocol] typing — no cross-module changes required."
  - severity: low
    claim: "Several test modules assign concrete objects directly to `store._table` (e.g. tests/test_storage.py:111, :1791, :1838, etc.) and `store._embedder` (tests/test_export.py:407 with `# type: ignore[attr-defined]`). With `_table: _LanceTableProtocol | None`, structural typing should accept these, but pyright may still flag certain Mock objects. Plan is silent on whether the pyright bar applies only to `mempalace_code/storage.py` or also to `tests/`."
    evidence: "tests/test_storage.py:110-111, 1769-1771, 1791-1793; tests/test_export.py:407; plan Design Notes line 53 explicitly scopes pyright to `mempalace_code/storage.py`."
    suggested_fix: "Make the pyright scope explicit in the (proposed new) pyright AC: 'pyright reports 0 errors for `mempalace_code/storage.py`; tests/ are out of scope for this task.' This matches the existing CLAUDE.md note that the pyright baseline is non-gating in CI."
