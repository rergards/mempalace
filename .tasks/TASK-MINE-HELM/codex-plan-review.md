verdict: READY
gaps: []

notes:
  - All five acceptance criteria (AC-1..AC-5) are observable and runnable via concrete pytest invocations; each has a matching `verification:` row plus regression coverage.
  - File list aligns with the affected surfaces: language catalog, detection, chunkers/symbols, miner shim re-exports, searcher validation, and MCP search tool schema text; supporting test files are all present in the repo.
  - `VALID_SYMBOL_TYPES` already contains `deployment` (searcher.py:217), so AC-3's `symbol_type='deployment'` expectation is consistent with existing K8s-style symbol extraction (`_extract_k8s_symbol` returns lowercase kind at symbols.py:711-712); no schema change is needed beyond adding `helm_chart`/`helm_values`.
  - `detect_language(filepath, content)` already receives a `Path` (orchestrator.py:156), so ancestor-walking for `Chart.yaml` is feasible when fixtures materialize the chart on disk; the plan acknowledges this via path-context wording, and AC-1/AC-4 imply real tempdir fixtures.
  - `task_contract` present with `mode: standard`; `contract_policy.flow: full_spdd`, `sync_gate: required`, `verification_path: automated` — all required fields are present.
  - `regression_plan.applies: true` with REG-1 and REG-2 collectively covering AC-1..AC-5; commands are concrete pytest/ruff invocations (no placeholders).
  - No backlog files (docs/BACKLOG.yaml, archive entries) appear in `files:`, `surfaces:`, or `touched_files:`; backlog completion is correctly out of scope.
  - Invariants explicitly guard against extension-map churn (.yaml/.yml/.tpl), Kubernetes precedence regressions, drawer schema drift, and external Helm execution — matches the codebase's `EXTENSION_LANG_MAP` and `_chunk_k8s_manifest` boundaries.
  - Synthetic detected language pattern already exists (`_SYNTHETIC_DETECTED_LANGUAGES = {"kubernetes"}` at language_catalog.py:134); the plan's "add helm as synthetic detected/searchable language" follows the same precedent.
