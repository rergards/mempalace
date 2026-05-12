slug: MINE-ANSIBLE
round: 1
date: 2026-05-12
commit_range: f22cc7c..HEAD
findings:
  - id: F-1
    title: "_extract_ansible_handler_symbol missing module-only fallback branch"
    severity: low
    location: "mempalace_code/mining/symbols.py:747"
    claim: |
      _extract_ansible_task_symbol has a fallback `if module: return (module, "ansible_task")` when
      no name is present, but _extract_ansible_handler_symbol did not have the equivalent branch.
      A handler with no name: key but a detectable module would silently return ("", "ansible_handler")
      instead of (module, "ansible_handler"), degrading search quality for name-less handlers.
    decision: fixed
    fix: "Added `if module: return (module, 'ansible_handler')` branch before the final empty return, matching _extract_ansible_task_symbol behavior. Added regression test test_extract_ansible_handler_symbol_module_only."

  - id: F-2
    title: "ansible_role symbol type registered in VALID_SYMBOL_TYPES and MCP description but never emitted"
    severity: medium
    location: "mempalace_code/searcher.py:230, mempalace_code/mcp/tools/search.py:173"
    claim: |
      VALID_SYMBOL_TYPES includes "ansible_role" and the MCP code_search tool description advertises
      it to clients, but no chunker or symbol extractor ever produces symbol_type='ansible_role'.
      A user filtering by symbol_type='ansible_role' will always get 0 results, contradicting the
      documentation. Role references from playbook 'roles:' sections exist only in verbatim chunk
      content, not in symbol metadata.
    decision: backlogged
    backlog_slug: MINE-ANSIBLE-ROLE-SYMBOL

  - id: F-3
    title: "Weak assertion in test_chunk_ansible_playbook_emits_play_per_chunk"
    severity: low
    location: "tests/test_miner.py:4548"
    claim: |
      The test exercised a 2-play playbook but asserted `len(chunks) >= 1` instead of `== 2`.
      A regression that collapsed both plays into one chunk would pass the test, defeating its
      purpose as a per-play splitting guard.
    decision: fixed
    fix: "Changed assertion to `assert len(chunks) == 2` to match the 2-play fixture."

totals:
  fixed: 2
  backlogged: 1
  dismissed: 0

fixes_applied:
  - "Added module-only fallback branch to _extract_ansible_handler_symbol in mempalace_code/mining/symbols.py"
  - "Added test_extract_ansible_handler_symbol_module_only in tests/test_symbol_extract.py"
  - "Tightened weak playbook split assertion from >= 1 to == 2 in tests/test_miner.py"

new_backlog:
  - slug: MINE-ANSIBLE-ROLE-SYMBOL
    summary: |
      ansible_role symbol type is registered in VALID_SYMBOL_TYPES and advertised in MCP docs
      but no chunker emits it. Either extract playbook role references as separate ansible_role
      chunks (satisfying REQ-2 from MINE-ANSIBLE), or remove the orphaned type registration to
      prevent misleading search consumers. Acceptance: code_search(symbol_type='ansible_role')
      returns drawers for playbooks that use roles:, OR the type is removed and MCP description
      and VALID_SYMBOL_TYPES no longer reference it.
