verdict: NEEDS_CHANGES

gaps:
  - severity: high
    claim: "AC-5 lacks a corresponding regression_plan.checks row linked via acceptance_ids."
    evidence: "docs/plans/QUAL-OPTIONAL-ANNOTATIONS.md regression_plan.checks (lines 188-203) — REG-1..REG-4 reference AC-1..AC-4; no REG row references AC-5."
    suggested_fix: "Add a REG-5 row to regression_plan.checks that mirrors VER-5 (pyright re-run) and lists acceptance_ids: [AC-5]; e.g. command `python -m pyright --pythonpath \"$(python -c 'import sys; print(sys.executable)')\"` proving 'no new non-optional defaults-to-None annotations were reintroduced'. Per the review meta-rule every acceptance criterion must be linked to a regression_plan.checks row."

notes:
  - "File list is complete: an independent grep for `: <NonOptionalType> = None` patterns under mempalace_code/ and tests/ returns exactly the 17 files listed in the plan (convo_miner, dialect, entity_registry, knowledge_graph, layers, mcp/tools/{architecture,graph,kg,read,search,write}, miner, onboarding, palace_graph, searcher, watcher, tests/test_cli.py). backup.py / spellcheck.py / storage.py only use already-correct Optional[...] or out-of-scope `Any = None` protocol placeholders, which the design notes explicitly exclude."
  - "All referenced test classes/functions exist: TestSearchTool.test_search_with_wing_filter, TestCodeSearchTool.test_code_search_combined_filters (test_mcp_server.py), TestNoneMetadataRobustness (test_searcher.py), TestTripleOperations.test_add_triple_with_dates / TestQueries.test_query_as_of_filters_expired / TestInvalidation.test_invalidate_sets_valid_to (test_knowledge_graph.py), TestDetectRoomCsprojMap.test_no_csproj_map_unchanged (test_miner.py), TestWatchAndMine.test_watch_passes_respect_gitignore_and_include_ignored (test_watcher.py), TestMineAllCommand.test_mine_all_basic (test_cli.py)."
  - "contract_policy is well-formed: flow=full_spdd, sync_gate=required, verification_path=automated; task_contract is present with mode=standard, requirements REQ-1..REQ-3 mapped to acceptance, invariants and risks captured."
  - "AC-1..AC-4 are observable (specific tests above). AC-5 is observable via pyright. No hidden TBD/deferred design. Design notes correctly bound out-of-scope cases (Optional[...] already-correct annotations, unannotated local sentinels, `Any = None` protocol placeholders, required-parameter widening, suppressions, CI gating changes)."
  - "No architectural contradictions found. Public CLI/MCP signatures and defaults are explicitly preserved via INV-1; None semantics for omitted filters/paths are explicitly preserved via INV-2; suppressions and Pyright-config weakening are explicitly forbidden via INV-3."
  - "Backlog metadata (docs/BACKLOG.yaml, archives) is not listed as a touched file or surface — correctly scoped."
