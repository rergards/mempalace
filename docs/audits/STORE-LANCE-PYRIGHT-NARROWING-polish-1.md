slug: STORE-LANCE-PYRIGHT-NARROWING
phase: polish
date: 2026-05-09
commit_range: b47d8bb~1..e02daaa
reverted: false
findings:
  - id: P-1
    title: "_embedder_handle() multi-line docstring"
    category: verbal
    location: "mempalace_code/storage.py:365"
    evidence: |
      """Return the initialized embedder or raise RuntimeError.

      Always call _ensure_embedder() before this method.
      """
    decision: fixed
    fix: "Collapsed two-paragraph docstring to one line capturing both the return contract and the precondition."

  - id: P-2
    title: "_require_db() single-call-site accessor helper"
    category: structural
    location: "mempalace_code/storage.py:349"
    evidence: "_require_db() is called only once, in _open_or_create() at line 393."
    decision: dismissed
    reason: "Single-use is intentional — the task explicitly calls for typed accessors to let Pyright narrow optional handles. An inline assert would also be one call site; the helper gives a clearer RuntimeError message. Consistent with _require_table() and _embedder_handle()."

  - id: P-3
    title: "_f() local helper routing through getattr in _where_to_arrow_mask"
    category: structural
    location: "mempalace_code/storage.py:731"
    evidence: |
      # Route through getattr to avoid PyArrow stub gaps for compute functions.
      def _f(name: str):
          return getattr(_pc, name)
    decision: dismissed
    reason: "Necessary Pyright workaround — PyArrow stubs do not cover all compute attributes. Used at 8+ call sites within the function. The comment explains the non-obvious WHY correctly."

totals:
  fixed: 1
  dismissed: 2
fixes_applied:
  - "Collapsed _embedder_handle() docstring from two paragraphs to one line"
