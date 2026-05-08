slug: STORE-LANCE-PYRIGHT-NARROWING
round: 1
date: 2026-05-09
commit_range: b47d8bb..HEAD
findings:
  - id: F-1
    title: "TC006 violations: unquoted type expressions in cast() calls"
    severity: low
    location: "mempalace_code/storage.py:312,340"
    claim: >
      Ruff TC006 requires type expressions inside typing.cast() to be quoted
      string literals. The implementation used bare names (_LanceDBConnectionProtocol
      and _EmbedderProtocol), which fail ruff check and indicate the cast targets
      are evaluated at runtime rather than deferred to type-checkers.
    decision: fixed
    fix: "Applied ruff --fix: wrapped both cast() type arguments in string quotes"

  - id: F-2
    title: "Ruff formatting violations in three code blocks"
    severity: low
    location: "mempalace_code/storage.py:486,609,779"
    claim: >
      ruff format --check flagged three blocks: the merge_insert() method chain in
      upsert(), the count_rows() call in delete_by_source_file(), and the $in branch
      in _where_to_arrow_mask(). Line-break placement didn't match project style.
    decision: fixed
    fix: "Applied ruff format: reformatted all three blocks to project line-length style"

  - id: F-3
    title: "_EmbedderProtocol.compute_source_embeddings return type is an approximation"
    severity: info
    location: "mempalace_code/storage.py:45"
    claim: >
      The Protocol declares compute_source_embeddings() -> list[list[float]] but the
      real LanceDB sentence-transformers embedder returns list[numpy.ndarray]. The
      _embed() method mitigates this via [list(v) for v in ...], converting to
      list[numpy.float32] lists, which PyArrow/LanceDB accept. The typing claim is
      a simplification but causes no runtime issue and avoids a numpy type dependency
      in the protocol definition.
    decision: dismissed

  - id: F-4
    title: "No direct tests for _require_db(), _require_table(), _embedder_handle() raising"
    severity: info
    location: "mempalace_code/storage.py:349-373"
    claim: >
      The three new accessor guards raise RuntimeError on None handles. These guards
      encode invariants that should never be violated in production (programming errors).
      No test verifies the error paths. Since they protect against invariant violations
      rather than production edge cases, the risk of not testing them is low.
    decision: dismissed

  - id: F-5
    title: "_OP_MAP in _where_to_arrow_mask is rebuilt on every non-$and/$or call"
    severity: info
    location: "mempalace_code/storage.py:756-763"
    claim: >
      The _OP_MAP dict is constructed per-call via _f() lookups. This replaces the
      original pc.equal etc. direct attribute access. Per-call getattr overhead is
      negligible given the function is not on the hot path, and the change was needed
      to avoid PyArrow stub gaps that prevented Pyright from narrowing pc.* calls.
    decision: dismissed

totals:
  fixed: 2
  backlogged: 0
  dismissed: 3

fixes_applied:
  - "TC006: quoted both cast() type arguments in storage.py lines 312 and 340"
  - "ruff format: reformatted merge_insert() chain, count_rows() call, and $in branch"

new_backlog: []
