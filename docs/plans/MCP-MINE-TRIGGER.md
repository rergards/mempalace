---
slug: MCP-MINE-TRIGGER
goal: "Expose mempalace_mine MCP tool so agents can trigger project re-mining without CLI access"
risk: low
risk_note: "Thin wrapper around existing mine() which already has incremental/full modes and returns stats; no new core logic"
files:
  - path: mempalace/mcp_server.py
    change: "Add tool_mine handler function and mempalace_mine entry in TOOLS dict"
  - path: tests/test_mcp_server.py
    change: "Add TestToolMine class: successful incremental mine, full mine, invalid directory, wing override"
acceptance:
  - id: AC-1
    when: "mempalace_mine is called with a valid project directory"
    then: "Returns {success: true, files_processed: N, files_skipped: N, drawers_filed: N, elapsed_secs: F} with correct counts"
  - id: AC-2
    when: "mempalace_mine is called with full=true on an already-mined directory"
    then: "files_skipped is 0 (all files re-processed regardless of hash match)"
  - id: AC-3
    when: "mempalace_mine is called with a non-existent directory path"
    then: "Returns {success: false, error: ...} without raising an exception"
  - id: AC-4
    when: "mempalace_mine is called with wing='custom_wing'"
    then: "Mined drawers are filed under the custom_wing wing (verified via search/status)"
  - id: AC-5
    when: "tools/list is called on the MCP server"
    then: "mempalace_mine appears in the tool list with correct input schema"
out_of_scope:
  - "Conversation mining (--mode convos) — separate tool if needed"
  - "Watch mode (long-running, not suitable for request-response MCP)"
  - "Dry-run mode (agents should mine for real, not preview)"
  - "include_ignored paths (can be added later if needed)"
---

## Design Notes

- **Handler function `tool_mine(directory, wing=None, full=False)`:**
  - Validates `directory` exists and is a directory; returns error dict if not.
  - Resolves `palace_path` from `_config.palace_path` (same as other handlers).
  - Calls `mine(project_dir=directory, palace_path=palace_path, wing_override=wing, incremental=not full, kg=_kg)`.
  - Wraps return in `{"success": True, **stats}`.
  - Catches exceptions and returns `{"success": False, "error": str(e)}`.

- **Parameter design:**
  - `directory` (required, string): absolute path to the project root to mine.
  - `wing` (optional, string): override wing name; defaults to directory basename (mine()'s behavior).
  - `full` (optional, boolean, default false): when true, forces full rebuild (`incremental=False`).

- **Registration:** Add to TOOLS dict after `mempalace_delete_wing` (in the write-tools section), before diary tools. The tool modifies palace state so it belongs in the write group.

- **KG integration:** Pass the module-level `_kg` singleton so type-extraction triples (Python class hierarchies, .NET types) are populated during mining.

- **Stdout suppression:** `mine()` prints progress to stdout. The MCP server uses stdio transport, so stdout writes would corrupt the JSON-RPC stream. Wrap the `mine()` call with `contextlib.redirect_stdout(io.StringIO())` (and stderr) to prevent corruption. The watcher already does this pattern (fd-level redirect in watcher.py).

- **Test approach:** Use the existing `_patch_mcp_server` + isolated `tmp_path` palace fixture pattern. Create a small temp project directory with a Python file, call `tool_mine`, verify stats and that drawers exist in the store.
