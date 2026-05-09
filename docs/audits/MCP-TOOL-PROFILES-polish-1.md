slug: MCP-TOOL-PROFILES
phase: polish
date: 2026-05-09
commit_range: 3294c89..0184296
reverted: false
findings:
  - id: P-1
    title: "_parse_comma_list docstring restates function name and body verbatim"
    category: verbal
    location: "mempalace_code/mcp_server.py:1752"
    evidence: |
      def _parse_comma_list(value: str) -> list[str]:
          """Split a comma-separated selector string into a non-empty list of stripped tokens."""
          return [tok.strip() for tok in value.split(",") if tok.strip()]
    decision: fixed
    fix: "Removed the single-line docstring; function name and body are self-documenting."

  - id: P-2
    title: "Spot-check loop in test_ac1_default_full_toolset is redundant after set equality"
    category: defensive
    location: "tests/test_mcp_server.py:2572"
    evidence: |
      assert names == frozenset(TOOLS)
      # Spot-check tools that must be present per AC-1
      for name in ("mempalace_delete_wing", "mempalace_mine", ...):
          assert name in names, f"{name} missing from default tools/list"
    decision: fixed
    fix: "Removed the for-loop; frozenset equality on the line above already guarantees all tools are present."

  - id: P-3
    title: "Inline comment in test_hidden_tool_is_distinct_from_unknown_tool restates test name"
    category: verbal
    location: "tests/test_mcp_server.py:2673"
    evidence: |
      # A truly unknown tool still returns -32601 but with different wording
    decision: fixed
    fix: "Removed the comment; the test name and assertions convey the same information."

  - id: P-4
    title: "KNOWN_PROFILES constant is a thin alias for frozenset(PROFILES)"
    category: structural
    location: "mempalace_code/mcp_tool_profiles.py:74"
    evidence: "KNOWN_PROFILES: frozenset[str] = frozenset(PROFILES)"
    decision: dismissed
    reason: "Exported as part of the module's public API; imported by name in tests and the error message in resolve_active_tools. The named constant is clearer at the call site than an inline frozenset(PROFILES)."

  - id: P-5
    title: "Module docstring body paragraph 1 partially restates module name"
    category: verbal
    location: "mempalace_code/mcp_tool_profiles.py:3"
    evidence: "Profiles are static, declarative subsets of the full TOOLS registry. They are resolved once at server startup; no runtime tool negotiation."
    decision: dismissed
    reason: "The second sentence ('no runtime tool negotiation') explicitly rules out an alternative design—this is non-obvious intent worth preserving. The paragraph is short enough that trimming the first sentence produces negligible benefit."

totals:
  fixed: 3
  dismissed: 2
fixes_applied:
  - "Removed redundant docstring from _parse_comma_list (mcp_server.py)"
  - "Removed defensive spot-check loop after frozenset equality in test_ac1_default_full_toolset (test_mcp_server.py)"
  - "Removed comment that restated the test name in test_hidden_tool_is_distinct_from_unknown_tool (test_mcp_server.py)"
