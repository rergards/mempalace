---
slug: CODE-SEARCH-LANG-CONFIG
goal: "Add yaml, json, toml to SUPPORTED_LANGUAGES so code_search language= filter works for config-file drawers"
risk: low
risk_note: "Purely additive change to a whitelist; no existing behaviour changes"
files:
  - path: mempalace/searcher.py
    change: "Add 'yaml', 'json', 'toml' to SUPPORTED_LANGUAGES set (config-file section)"
  - path: mempalace/mcp_server.py
    change: "Update language description string in mempalace_code_search input schema to include yaml, json, toml examples"
  - path: tests/test_mcp_server.py
    change: "Add test asserting code_search(language='yaml') succeeds; assert 'cobol' still fails in existing test"
acceptance:
  - id: AC-1
    when: "code_search(language='yaml') is called with a seeded palace"
    then: "Returns a results dict (no 'error' key)"
  - id: AC-2
    when: "code_search(language='cobol') is called"
    then: "Returns error with 'supported_languages' key (existing test still passes)"
  - id: AC-3
    when: "ruff check + ruff format --check run on modified files"
    then: "No violations"
out_of_scope:
  - "Adding new miner language mappings (miner.py already maps .yaml/.json/.toml correctly)"
  - "Adding markdown, text, or other non-config languages"
  - "Changing VALID_SYMBOL_TYPES"
---

## Design Notes

- `SUPPORTED_LANGUAGES` in `searcher.py:157` is the sole validation gate. Adding the three strings is the entire backend fix.
- The miner already emits `language="yaml"` for `.yaml`/`.yml`, `language="json"` for `.json`, and `language="toml"` for `.toml` (see `miner.py:39–42`). No miner changes needed.
- MCP schema description at `mcp_server.py:653` is informational only (no machine validation there), but should be updated to list the new values so callers know they're valid.
- The existing `test_code_search_invalid_language` test asserts "cobol" is rejected and "python" is in `supported_languages`. After the fix, "yaml"/"json"/"toml" will also appear in that list — the test still passes unchanged.
- New test should seed at least one drawer with `language="yaml"` (or reuse the `code_seeded_collection` fixture if it already has config-file drawers; otherwise add a minimal fixture entry).
- No migration needed: LanceDB stores language as a string field; no schema change.
