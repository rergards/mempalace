slug: STORE-OPTIMIZE-CONTRACT
round: 1
date: 2026-05-09
commit_range: 4546c75..HEAD
findings:
  - id: F-1
    title: "OptimizeResult.message field is unused dead code"
    severity: low
    location: "mempalace_code/storage.py:197"
    claim: >
      OptimizeResult was given a `message: str = field(default="")` field that
      optimize_store() never populates and no caller reads. It adds complexity
      without benefit and violates the project's no-extra-abstractions rule
      (CLAUDE.md). The `field` import from dataclasses was also unnecessary.
    decision: fixed
    fix: >
      Removed the `message` field from OptimizeResult and dropped the now-unused
      `field` import. All OptimizeResult constructions already used positional
      keyword args for `ok` and `supported` only, so no call sites needed updates.

  - id: F-2
    title: "test_mine_convos_calls_optimize_once has stale docstring and weak assertion"
    severity: low
    location: "tests/test_convo_miner.py:30"
    claim: >
      After the refactor the test docstring still read "calls collection.optimize()
      exactly once" (referencing the old direct call), while the implementation now
      routes through optimize_store(). The assertion `mock_store.safe_optimize.called
      or mock_store.optimize.called` was disjunctive and did not enforce the
      call-count invariant promised by the docstring. A regression that called
      optimize_store() twice would pass this assertion.
    decision: fixed
    fix: >
      Updated docstring to "routes optimization through optimize_store() exactly once".
      Replaced the disjunctive assertion with a patch on optimize_store and
      mock_adapt.assert_called_once(), which directly verifies the new contract.

  - id: F-3
    title: "Duplicate backup_first=True test pairs in test_miner.py and test_convo_miner.py"
    severity: info
    location: "tests/test_convo_miner.py:55 and tests/test_convo_miner.py:89; tests/test_miner.py analogous"
    claim: >
      test_mine_convos_default_calls_safe_optimize_backup_first and
      test_mine_convos_default_calls_optimize_store_backup_first (and the miner
      analogues) both patch optimize_store and assert backup_first=True with
      identical setup. The second test in each pair adds a more complex dual
      assertion (positional OR keyword) but tests no new behaviour.
    decision: dismissed
    fix: ~

totals:
  fixed: 2
  backlogged: 0
  dismissed: 1
fixes_applied:
  - "Removed unused OptimizeResult.message field and redundant `field` import from storage.py"
  - "Replaced stale disjunctive assertion in test_mine_convos_calls_optimize_once with optimize_store patch + assert_called_once()"
new_backlog: []
