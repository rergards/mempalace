slug: REFAC-MINER-MODULES
round: 1
date: 2026-05-11
commit_range: 179f43b..22ff152
findings:
  - id: F-1
    title: "Codex: shim omits ~60 private legacy names that were importable from miner.py"
    severity: info
    location: "mempalace_code/miner.py:1"
    claim: >
      Codex review flagged that names like _split_yaml_documents, TS_IMPORT, FENCED_CODE_MD,
      _DOTNET_PROJECT_FILE_EXTS, and ~55 others are not re-exported by the compatibility shim.
      The task contract requires existing direct imports to keep resolving.
    decision: dismissed
    fix: >
      Grep across all tests and source files shows none of the ~60 flagged names are
      actually imported from mempalace_code.miner anywhere in the repo. The shim contract
      is "preserve existing direct imports used by CLI, watcher, convo, KG, and tests"
      — not "re-export every internal symbol that was previously a module-level name."
      All 808+145+8 regression tests pass, confirming no actual import breakage.

  - id: F-2
    title: "Compatibility test missing 13 names that ARE re-exported and ARE imported by tests"
    severity: medium
    location: "tests/test_miner_modules.py:10"
    claim: >
      test_miner_compatibility_exports_existing_import_surface imports only a subset of the
      names re-exported by miner.py. Names actively used by test_treesitter.py (chunk_code),
      test_symbol_extract.py (SWIFT_BOUNDARY, chunk_code), test_chunking.py (TS_BOUNDARY,
      GO_BOUNDARY, adaptive_merge_split, chunk_adaptive_lines, chunk_prose),
      test_miner.py (_subtree_glob_prefix, _build_csproj_room_map, _chunk_k8s_manifest,
      _detect_sln_wing, _detect_batch_size), and test_kg_extract.py (parse_dotnet_project_file)
      were not asserted by the compatibility guard. A future accidental removal from the shim
      would not be caught by this test.
    decision: fixed
    fix: >
      Added all 13 missing names to the import list in
      test_miner_compatibility_exports_existing_import_surface. Callables asserted with
      callable(), boundary regex constants asserted as re.Pattern instances.
      All 8 test_miner_modules.py tests continue to pass.

  - id: F-3
    title: "Pre-existing: Python nested generic stripping fails on multi-level brackets"
    severity: medium
    location: "mempalace_code/mining/kg_extract.py:394"
    claim: >
      In _python_type_rels(), `re.sub(r"\[.*?\]", "", bases_str)` uses a non-greedy match
      that stops at the first `]`. For a class like `Foo(Generic[Dict[str, List[int]]])`,
      the substitution leaves malformed remnants instead of stripping the full bracket tree,
      producing incorrect or empty base-class triples. This pre-existed in miner.py and was
      carried verbatim into mining/kg_extract.py.
    decision: backlogged
    backlog_slug: KG-EXTRACT-PYTHON-NESTED-GENERIC

  - id: F-4
    title: "Pre-existing: Java symbol pattern has catastrophic backtracking risk"
    severity: medium
    location: "mempalace_code/mining/symbols.py:98"
    claim: >
      The Java extraction pattern combines a negative lookahead with `(?:(?:public|...)\s+)*`
      (zero-or-more optional modifiers). On pathological input with many repeated modifier-like
      tokens and spaces, the regex engine can backtrack exponentially. This pre-existed in
      miner.py and was carried verbatim into mining/symbols.py.
    decision: backlogged
    backlog_slug: SYMBOL-JAVA-REDOS-RISK

totals:
  fixed: 1
  backlogged: 2
  dismissed: 1

fixes_applied:
  - "tests/test_miner_modules.py: extended test_miner_compatibility_exports_existing_import_surface
    to cover all 13 names used by tests but missing from the compatibility assertion (chunk_code,
    parse_dotnet_project_file, _subtree_glob_prefix, SWIFT_BOUNDARY, TS_BOUNDARY, GO_BOUNDARY,
    adaptive_merge_split, chunk_adaptive_lines, chunk_prose, _build_csproj_room_map,
    _chunk_k8s_manifest, _detect_sln_wing, _detect_batch_size)"

new_backlog:
  - slug: KG-EXTRACT-PYTHON-NESTED-GENERIC
    summary: >
      Fix Python nested generic stripping in kg_extract._python_type_rels() so that
      class Foo(Generic[Dict[str, List[int]]]) produces correct base-class KG triples
      instead of malformed remnants.

  - slug: SYMBOL-JAVA-REDOS-RISK
    summary: >
      Audit and harden the Java symbol extraction regex in symbols.py to eliminate the
      catastrophic backtracking risk from the negative lookahead combined with the
      zero-or-more optional modifier chain. Replace with an atomic or possessive group
      or restructured pattern with a verified benchmark against the existing Java test corpus.
