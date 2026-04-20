slug: MCP-MINE-TRIGGER
round: 1
date: "2026-04-20"
commit_range: a888b0a..58a4d0b
findings:
  - id: F-1
    title: "from pathlib import Path declared inside tool_mine() instead of module level"
    severity: low
    location: "mempalace/mcp_server.py:418"
    claim: >
      Path was imported with a function-scoped `from pathlib import Path` statement inside
      tool_mine(). All other modules in the file use module-level imports. The deferred import
      causes a minor re-import cost on every call and is inconsistent with the rest of the
      file's style. No functional impact, but it's out of place given that os, sys, and all
      other stdlib symbols are imported at the top.
    decision: fixed
    fix: >
      Moved `from pathlib import Path` to the module-level import block (line 37) and removed
      the deferred import from inside tool_mine().

  - id: F-2
    title: "_mine_quiet: fd resource leak if os.dup() fails before try block"
    severity: info
    location: "mempalace/mcp_server.py:378-380"
    claim: >
      The setup sequence `devnull = os.open(...)`, `old_out = os.dup(1)`, `old_err = os.dup(2)`
      runs before the try block. If `os.dup(1)` raises (e.g. EMFILE — fd table full), `devnull`
      leaks. If `os.dup(2)` raises, both `devnull` and `old_out` leak. In practice os.dup() on
      fds 1 and 2 does not fail unless the process is out of fds, at which point much worse
      problems are already present. This is an observation, not an actionable bug.
    decision: dismissed

totals:
  fixed: 1
  backlogged: 0
  dismissed: 1

fixes_applied:
  - "Move `from pathlib import Path` to module-level imports in mcp_server.py"

new_backlog: []
