slug: CODE-TREESITTER-EXPAND
round: 1
date: 2026-04-14
commit_range: d4f9b7c..4bd4ad5
findings:
  - id: F-1
    title: "Too-permissive assertion in no-definitions fallback tests (Go and Rust)"
    severity: low
    location: "tests/test_chunking.py:1376,1588"
    claim: >
      test_ast_go_no_definitions_falls_back and test_ast_rust_no_definitions_falls_back
      both assert chunk.get("chunker_strategy") in ("treesitter_adaptive_v1",
      "treesitter_v1"). The fallback path in _chunk_go_treesitter and
      _chunk_rust_treesitter always tags chunks "treesitter_adaptive_v1"; the
      "treesitter_v1" branch can never appear in a no-definitions file. The
      too-permissive set means a regression where the wrong tag is applied would
      still pass the test.
    decision: fixed
    fix: >
      Tightened both assertions to == "treesitter_adaptive_v1". Removed the
      dead "treesitter_v1" alternative from both no-definitions fallback test
      assertions. No logic change, test-quality fix only.

  - id: F-2
    title: "Missing negative tests for detached-comment gap check (Go and Rust)"
    severity: low
    location: "tests/test_chunking.py:1361,1557"
    claim: >
      GO_AST_COMMENT_ATTACHED contains "// Detached comment — blank line
      separates it." above func standalone(), and RUST_AST_ATTRIBUTE_ATTACHED
      contains "// Standalone comment with blank line above." above
      default_config(). Neither fixture has a test asserting the detached
      comment is NOT absorbed into the following declaration's chunk. If the
      blank-line gap check (b'\n\n' in gap) were removed from either chunker,
      no existing test would fail. This mirrors the gap filed as
      CODE-TREESITTER-PYTHON-DETACH-TEST for Python.
    decision: backlogged
    backlog_slug: CODE-TREESITTER-GO-RUST-DETACH-TEST

  - id: F-3
    title: "Rust const_item and static_item absent from DEFINITION_TYPES"
    severity: info
    location: "mempalace/miner.py:886"
    claim: >
      _chunk_rust_treesitter's DEFINITION_TYPES covers fn, struct, enum,
      trait, impl, mod, and type_item but omits const_item and static_item.
      Module-level Rust constants (pub const FOO: u32 = 42;) and statics are
      absorbed into adjacent chunks rather than becoming individual chunk
      boundaries. Go's counterpart (_chunk_go_treesitter) DOES include
      const_declaration and var_declaration, creating an asymmetry. The
      omission is within AC spec ('fn, struct, enum, trait, impl, mod
      boundaries') but leaves a gap for large constant tables.
    decision: backlogged
    backlog_slug: CODE-TREESITTER-RUST-CONST-STATIC

totals:
  fixed: 1
  backlogged: 2
  dismissed: 0

fixes_applied:
  - "Tightened test_ast_go_no_definitions_falls_back and test_ast_rust_no_definitions_falls_back assertions from `in ('treesitter_adaptive_v1', 'treesitter_v1')` to `== 'treesitter_adaptive_v1'`"

new_backlog:
  - slug: CODE-TREESITTER-GO-RUST-DETACH-TEST
    summary: "Add negative tests for detached-comment gap detection in Go and Rust AST chunkers (tests/test_chunking.py)"
  - slug: CODE-TREESITTER-RUST-CONST-STATIC
    summary: "Add const_item and static_item to Rust AST chunker DEFINITION_TYPES for parity with Go const/var handling"
