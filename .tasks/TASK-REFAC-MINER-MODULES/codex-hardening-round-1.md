## 1. New Findings

### P2 / High - Compatibility shim no longer exports the full legacy miner import surface

`mempalace_code/miner.py:5` now manually re-exports a curated subset of names from `mempalace_code.mining.*`. The old `miner.py` defined many additional top-level helpers/constants that were importable before the refactor, but the shim omits them. Examples from the scoped diff include `_split_yaml_documents`, `_clean_markdown_heading`, `_markdown_section_metadata`, `_split_oversized`, `_split_base_list`, `_join_continuation_lines`, `_csharp_type_rels`, `_python_type_rels`, `TS_IMPORT`, `FENCED_CODE_MD`, `MERMAID_CODE_MD`, `TABLE_ROW_MD`, `_DOTNET_PROJECT_FILE_EXTS`, `_SLN_PROJECT_EXTS`, and several extraction regex tables. Any downstream code importing these existing `mempalace_code.miner` names now gets `ImportError`, even though the task contract says existing direct imports from `mempalace_code.miner` must keep resolving. The new import-contract test only covers a small selected subset, so this regression is not guarded.

Suggested fix: either re-export every previous top-level non-module name from `mempalace_code/miner.py`, or explicitly define a narrower compatibility contract and add a targeted breaking-change note. For this task's stated compatibility goal, re-exporting the previous top-level helpers is the safer fix.

## 2. Known Issues Map Status

No previous audit was present at `docs/audits/REFAC-MINER-MODULES-round-0.md` in this snapshot, so no duplicate suppression was needed from prior findings.

Backlog/context reviewed: `docs/plans/REFAC-MINER-MODULES.md`. The finding maps to `REQ-1`, `INV-1`, and `RISK-1` in that plan.

## 3. Evidence Reviewed

- Scoped diff: `.tasks/TASK-REFAC-MINER-MODULES/codex-hardening-round-1.diff`
- Scoped files manifest: `.tasks/TASK-REFAC-MINER-MODULES/codex-hardening-round-1-files.txt`
- Relevant plan/backlog context: `docs/plans/REFAC-MINER-MODULES.md`
- Touched implementation files inspected: `mempalace_code/miner.py`, `mempalace_code/mining/*.py`, `mempalace_code/cli.py`, `mempalace_code/convo_miner.py`, `mempalace_code/watcher.py`, `mempalace_code/room_detector_local.py`
- Touched tests inspected: `tests/test_miner_modules.py`, `tests/test_miner.py`, `tests/test_cli.py`, `tests/test_watcher.py`
- Static comparison: parsed removed top-level names from the old `miner.py` hunk and compared them with the new shim import list; 60 previous top-level names are not re-exported.

Targeted pytest command attempted:

`python -m pytest tests/test_miner_modules.py tests/test_cli.py::TestMineSpellcheckFlags tests/test_watcher.py::TestIsRelevantChange::test_app_scan_excludes_match_scan_project tests/test_miner.py::test_scan_project_does_not_reinclude_file_from_ignored_directory tests/test_miner.py::test_scan_project_can_include_exact_file_without_known_extension -q`

Result caveat: the isolated snapshot lacks unscoped package files such as `mempalace_code/__init__.py`, so Python imported an installed `/Users/rerg/dev/mempalace/mempalace_code` package instead of this snapshot. The run therefore failed with `ModuleNotFoundError: No module named 'mempalace_code.mining'`; I treated that as an environment/snapshot limitation, not as a scoped-diff finding.

## 4. Residual Risks

- I could not execute the scoped tests against the snapshot package because the snapshot omits unscoped package files required for normal import resolution.
- Packaging metadata was not present in the scoped manifest. If the real project uses an explicit package list rather than discovery, `mempalace_code.mining` may also need packaging updates outside this diff.
- Because this is a large split, behavior-preservation confidence depends on running the plan's VER/REG commands in a full checkout after the shim export issue is addressed.

## 5. Convergence Recommendation

Do not converge yet. The implementation is close, but the shim currently narrows the old `mempalace_code.miner` import surface despite the task's compatibility requirement. Fix the re-export gap, then run the planned targeted verification in a full checkout.

## 6. Suggested Claude Follow-Up

Update `mempalace_code/miner.py` to re-export the omitted legacy top-level helpers/constants from the new owning modules, and extend `tests/test_miner_modules.py` with a regression list generated from the previous `miner.py` top-level API so the compatibility surface cannot silently shrink again.
