---
slug: CODE-SMART-CHUNK-VAR-BOUNDARY
goal: "Add var\\s+\\w+\\s*[:=] arm to TS_BOUNDARY so top-level non-exported var declarations create chunk boundaries in TS/JS"
risk: low
risk_note: "One-line regex append to TS_BOUNDARY; tree-sitter path is unaffected; var is rare in modern TS/JS"
files:
  - path: mempalace/miner.py
    change: "Append r\"|var\\s+\\w+\\s*[:=]\" to TS_BOUNDARY after the existing let arm (line ~426)"
  - path: tests/test_chunking.py
    change: "Add test_ts_var_toplevel_boundary: verify TS_BOUNDARY matches var declarations and chunk_code produces a boundary at top-level var"
acceptance:
  - id: AC-1
    when: "chunk_code() (regex path, tree-sitter disabled) is called on a TS/JS file with a top-level non-exported var declaration"
    then: "A chunk boundary is produced at the var line; the var declaration appears in its own chunk (or starts a new chunk)"
  - id: AC-2
    when: "TS_BOUNDARY.match() is called with 'var foo = ...' at column 0"
    then: "The regex matches"
  - id: AC-3
    when: "All existing chunk_code TypeScript/JavaScript tests are run after the change"
    then: "All pass unchanged (no regressions)"
  - id: AC-4
    when: "ruff check mempalace/ tests/ is run after the change"
    then: "No lint errors in modified files"
out_of_scope:
  - "Tree-sitter TS/JS path — already correct; var_declaration is a top-level AST node and is naturally emitted"
  - "Indented var inside function/method bodies — safe because TS_BOUNDARY uses ^ anchor with re.MULTILINE against the raw (non-stripped) line, so indented lines never match"
  - "export var — already handled by the export\\s+... arm on line 419"
  - "GO_BOUNDARY or any other language boundary patterns"
---

## Design Notes

- **Why the `^` anchor is sufficient**: Unlike `GO_BOUNDARY`, which matches against `stripped = line.strip()` (enabling false positives from indented body-level `var`), `TS_BOUNDARY` is applied against the raw line using `re.MULTILINE`. A `var` inside a function body is indented (e.g. `    var x = 1`) and the `^` anchor forces the match to start at column 0, so it will not fire.

- **Insertion point**: Add `r"|var\s+\w+\s*[:=]"` immediately after the `r"|let\s+\w+\s*[:=]"` arm (currently line 426) to keep the const/let/var trio together.

- **Pattern**: `var\s+\w+\s*[:=]` mirrors the existing `const`/`let` arms exactly — `\w+` for the identifier, `\s*[:=]` to match both typed declarations (`var x: T = ...`) and plain assignment (`var x = ...`).

- **Test strategy**: Use `monkeypatch` to force the regex path (consistent with `test_go_var_in_body_no_spurious_split` and related tests) for a deterministic result independent of whether `tree-sitter-typescript` is installed. Two assertions: (a) `TS_BOUNDARY.match("var foo = ...")` succeeds (unit test on the regex), (b) `chunk_code()` on a multi-definition TS file with a top-level `var` produces a chunk that starts at or includes the `var` line.

- **Chunk size caveat**: `adaptive_merge_split` will merge tiny chunks up to `TARGET_MAX` (2500 chars), so a single-line `var` may be merged into an adjacent chunk. The test source must be large enough (or the var block long enough) to survive merging, or the test should verify `TS_BOUNDARY.match` directly rather than counting final chunks. Use the direct regex check for AC-2 and a sufficiently padded source for AC-1.
