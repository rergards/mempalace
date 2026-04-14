---
slug: CODE-SEARCH-LANG-CPP
goal: "Add .c/.cpp to EXTENSION_LANG_MAP and READABLE_EXTENSIONS so mined C/C++ files get language='c'/'cpp' and code_search(language='cpp') returns results"
risk: low
risk_note: "Purely additive — new entries in existing maps/sets, new extract patterns; no existing language paths touched"
files:
  - path: mempalace/miner.py
    change: "Add '.c': 'c', '.cpp': 'cpp', '.h': 'c', '.hpp': 'cpp' to EXTENSION_LANG_MAP; add same extensions to READABLE_EXTENSIONS; add _C_EXTRACT and _CPP_EXTRACT regex pattern lists; register both in _LANG_EXTRACT_MAP"
  - path: tests/test_lang_detect.py
    change: "Extend parametrize table to include .c→c, .cpp→cpp, .h→c, .hpp→cpp"
  - path: tests/test_symbol_extract.py
    change: "Add tests for C struct/enum/function and C++ class/struct/enum extraction"
  - path: tests/test_mcp_server.py
    change: "Add test_code_search_cpp_language: seed a drawer with language='cpp', assert code_search(language='cpp') returns results (mirrors test_code_search_yaml_language pattern)"
acceptance:
  - id: AC-1
    when: "detect_language(Path('foo.c')) / detect_language(Path('foo.cpp')) is called"
    then: "Returns 'c' / 'cpp' respectively"
  - id: AC-2
    when: "code_search(language='cpp') is called with at least one cpp-language drawer seeded"
    then: "Returns a results dict with no 'error' key and len(results) > 0"
  - id: AC-3
    when: "extract_symbol('struct Node { int val; };\\n', 'c') is called"
    then: "Returns ('Node', 'struct')"
  - id: AC-4
    when: "extract_symbol('class Foo {\\n};\\n', 'cpp') is called"
    then: "Returns ('Foo', 'class')"
  - id: AC-5
    when: "ruff check + ruff format --check run on modified files"
    then: "No violations"
out_of_scope:
  - "Tree-sitter AST chunking for C/C++ (miner uses regex extraction; tree-sitter path is a separate feature)"
  - "Adding less-common extensions (.cc, .cxx, .hh, .hxx) — can be added later"
  - "Changing SUPPORTED_LANGUAGES in searcher.py (already contains 'c' and 'cpp')"
  - "Adding 'method' symbol_type detection for C++ member functions (ClassName::method pattern) — first-pass keeps it simple"
---

## Design Notes

- `EXTENSION_LANG_MAP` at `miner.py:25` controls which extension → language tag is stored per drawer. Adding `.c`/`.cpp` here is the minimal fix that makes mining produce the right `language` field.
- `READABLE_EXTENSIONS` at `miner.py:56` is the gate that determines whether a file is read at all during a scan. Without adding `.c`/`.cpp` here, the extension map entry is never reached (files are silently skipped). Both sets must be updated together.
- `SUPPORTED_LANGUAGES` at `searcher.py:157` already contains `"c"` and `"cpp"` — no change needed there.
- Header files (`.h`, `.hpp`) are included because they are frequently the most symbol-rich C/C++ files. `.h` maps to `"c"` (safe default; most headers are C-compatible); `.hpp` maps to `"cpp"`.
- `_C_EXTRACT` patterns — reliable patterns only; C has no `func` keyword so function detection uses a heuristic `return_type name(`:
  ```python
  _C_EXTRACT = [
      (re.compile(r"^struct\s+(\w+)", re.MULTILINE), "struct"),
      (re.compile(r"^enum\s+(\w+)", re.MULTILINE), "enum"),
      # heuristic: word chars, optional *, then name( — matches most top-level C defs
      (re.compile(r"^[\w][\w\s*]+\s(\w+)\s*\([^;]*\)\s*\{", re.MULTILINE), "function"),
  ]
  ```
- `_CPP_EXTRACT` — superset of C patterns plus class:
  ```python
  _CPP_EXTRACT = [
      (re.compile(r"^class\s+(\w+)", re.MULTILINE), "class"),
      (re.compile(r"^struct\s+(\w+)", re.MULTILINE), "struct"),
      (re.compile(r"^enum\s+(?:class\s+)?(\w+)", re.MULTILINE), "enum"),
      (re.compile(r"^[\w][\w\s*:<>]+\s(\w+)\s*\([^;]*\)\s*\{", re.MULTILINE), "function"),
  ]
  ```
- `_LANG_EXTRACT_MAP` at `miner.py:576`: add `"c": _C_EXTRACT, "cpp": _CPP_EXTRACT`.
- The function heuristic regex will false-positive on some macros and multi-line declarations, but it mirrors the pragmatic level of accuracy used for other languages (e.g. Rust's pattern also captures some non-functions). First-pass quality is adequate for semantic search use.
- Test pattern: `test_code_search_cpp_language` should follow `test_code_search_yaml_language` (line 560) — seed one drawer directly into `code_seeded_collection` with `language="cpp"`, then assert `code_search(language="cpp")` returns results.
