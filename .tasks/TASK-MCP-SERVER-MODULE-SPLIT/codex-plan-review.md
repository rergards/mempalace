verdict: READY

summary: |
  The plan is a no-behavior-change refactor with a clear target shape (mempalace_code/mcp
  package + mempalace_code/mcp_server.py compatibility shim). Acceptance criteria are
  observable via direct imports, JSON-RPC handle_request calls, and a subprocess that
  asserts sys.modules absence — all testable mechanically. Files list covers the source
  modules, the four affected test files (test_mcp_server, test_mcp_tool_profiles,
  test_e2e, test_packaging_namespace), and a new test_mcp_registry. Architectural
  invariants are preserved: registry shape (description/input_schema/handler) is
  unchanged, registry insertion order matches the current TOOLS dict (which already
  groups by family: read → kg → architecture → graph → search → write → diary),
  lazy startup is explicitly preserved, _NOISE_KEYS / int-coerce / hidden-tool error
  branches are kept under dispatch.py, and the mempalace.mcp_server star-import shim
  continues to work via mcp_server.py re-exports. Out-of-scope is tightly drawn.

  No critical or high-severity gaps were found. A handful of medium/low items are
  worth pinning down during implementation but do not block starting work.

gaps:
  - severity: medium
    claim: "Plan lists runtime patching seams as `_config`, `_kg`, `_store`, `_store_read_only`, but existing tests also monkeypatch `_get_store` directly to inject failure stores."
    evidence: "tests/test_mcp_server.py:2054,2127 use `monkeypatch.setattr(mcp_server, '_get_store', ...)`. Plan design note line: 'monkeypatch `mempalace_code.mcp.runtime._config`, `_kg`, `_store`, and `_store_read_only`' (docs/plans/MCP-SERVER-MODULE-SPLIT.md design notes)."
    suggested_fix: "In the design notes, explicitly say `_get_store` patches must move to `mempalace_code.mcp.runtime._get_store` as well, since family handlers will import `_get_store` from runtime — patching it on `mcp_server` will not propagate after the split."
  - severity: low
    claim: "File list does not name `mempalace/mcp_server.py` (legacy shim) even though AC-10 depends on it staying identity-compatible."
    evidence: "mempalace/mcp_server.py:1-11 does `from mempalace_code.mcp_server import *` plus `import main`; AC-10 (plan acceptance) asserts `import mempalace.mcp_server` resolves to the same handle_request/main."
    suggested_fix: "Add an explicit 'no change required' file entry for `mempalace/mcp_server.py` so reviewers know AC-10 was considered and the shim was deliberately left as a star-import."
  - severity: low
    claim: "Plan says read.py owns `tool_get_aaak_spec` 'plus their registry specs', but tool_get_aaak_spec has no entry in TOOLS — it is only a compatibility-imported helper used by tests."
    evidence: "mempalace_code/mcp_server.py:298-302 defines `tool_get_aaak_spec` outside the TOOLS dict; tests/test_mcp_server.py:314 imports it directly."
    suggested_fix: "Clarify in the design notes that read.py exposes `tool_get_aaak_spec` as a non-registry helper (still re-exported from mcp_server for the existing direct-import tests), so the implementer does not invent a phantom registry entry."
  - severity: low
    claim: "AC-7 requires that `mempalace_code.miner` is absent from sys.modules after initialize+tools/list, but the plan does not state which test file owns the new/updated subprocess assertion for the package-split arrangement."
    evidence: "Existing subprocess lazy-startup tests live in tests/test_mcp_server.py:2340+ and tests/test_mcp_server.py:2756+ (test_ac1b_minimal_profile_lazy_startup); plan acceptance AC-7 + plan files list show test_mcp_server.py is updated, but does not name lazy-startup as covered."
    suggested_fix: "In the design notes, name the existing lazy-startup subprocess tests under tests/test_mcp_server.py as the AC-7 verification surface and note that they must keep passing unmodified except for the import path."
  - severity: low
    claim: "Plan does not state where active_registry / startup-flag end-to-end coverage for AC-4 (hidden delete_wing returns -32601 with profile-disabled message) currently lives or where it will live after the split."
    evidence: "Plan AC-4 + handle_request branch in mempalace_code/mcp_server.py:1704-1714 distinguishes 'Tool not enabled by the active MCP profile' vs 'Unknown tool'; tests/test_mcp_tool_profiles.py:19,27,333 imports TOOLS but the plan does not state whether the hidden-tool dispatch assertion is in test_mcp_tool_profiles.py or test_mcp_registry.py."
    suggested_fix: "Specify which test file owns the AC-4 dispatch assertion (recommend tests/test_mcp_registry.py since it is the new file and the plan already lists 'duplicate-name rejection' there) so the implementer does not have to guess."
