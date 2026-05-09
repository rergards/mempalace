slug: MCP-SERVER-MODULE-SPLIT
round: 1
date: 2026-05-09
commit_range: 6a4e9cf..HEAD
findings:
  - id: F-1
    title: "_active_registry or TOOLS falsy-dict fallback"
    severity: info
    location: "mempalace_code/mcp/dispatch.py:28"
    claim: >
      handle_request resolves the active registry with
      `_active_registry or TOOLS`. If _active_registry were set to {} (empty
      dict), Python's truthiness test would fall back to the full TOOLS
      registry instead of the empty profile. In practice this cannot occur:
      resolve_active_tools raises ValueError on an empty result, and main()
      exits on ValueError before the loop starts. Pre-existing code from the
      original mcp_server.py; not introduced by the split.
    decision: dismissed

  - id: F-2
    title: "Shim re-exports mutable globals (_kg, _store) by value"
    severity: info
    location: "mempalace_code/mcp_server.py:14-26"
    claim: >
      The shim binds module-level names such as _kg, _store, _store_read_only
      at import time, capturing their initial None/False values. Reassigning
      runtime._kg at runtime does not update mcp_server._kg. The plan
      explicitly documents this: 'assignment to mcp_server._config is no longer
      a supported test seam.' All tests correctly patch mempalace_code.mcp.runtime
      attributes directly. No regression.
    decision: dismissed

  - id: F-3
    title: "category_map dict duplicated in tool_find_references and tool_explain_subsystem"
    severity: low
    location: "mempalace_code/mcp/tools/architecture.py:102-113 and 217-228"
    claim: >
      Both handlers define an identical 10-entry category_map dict inline. A
      future update to one that misses the other would silently diverge. This
      was pre-existing in the original single-file mcp_server.py; the split did
      not introduce it but made the duplication more visible.
    decision: dismissed

  - id: F-4
    title: "int(value) coercion raises ValueError for float-string inputs"
    severity: info
    location: "mempalace_code/mcp/dispatch.py:92-93"
    claim: >
      The type coercion block calls int(value) for integer-declared parameters
      when the value is not already an int. If a malformed MCP client sends a
      float-string like "5.7" for an integer field, int("5.7") raises ValueError,
      which the outer except catches and returns a generic -32000 Internal tool
      error instead of a more informative -32602. Well-behaved MCP clients send
      JSON numbers, not strings. Pre-existing code copied faithfully from the
      original mcp_server.py.
    decision: dismissed

totals:
  fixed: 0
  backlogged: 0
  dismissed: 4

fixes_applied: []

new_backlog: []
