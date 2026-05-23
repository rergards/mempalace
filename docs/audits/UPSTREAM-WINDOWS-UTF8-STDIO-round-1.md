slug: UPSTREAM-WINDOWS-UTF8-STDIO
round: 1
date: 2026-05-23
commit_range: 2dd18db..HEAD
findings:
  - id: F-1
    title: "test_mcp_stdout_write_uses_ensure_ascii_false is a dead test — never exercises dispatch.main()"
    severity: medium
    location: "tests/test_stdio.py:174"
    claim: >
      The test contains `dispatch.main.__wrapped__() if hasattr(dispatch.main, "__wrapped__") else None`
      which evaluates to None and does nothing. The body then only validates Python stdlib json.dumps
      behavior on a locally-constructed dict, not the dispatch code. Reverting ensure_ascii=False on
      dispatch.py:212 would not cause this test to fail.
    decision: fixed
    fix: >
      Rewrote the test to call dispatch.main(argv=[]) with sys.stdin mocked to deliver one
      tools/call request and EOF, dispatch.TOOLS patched to a single fake tool returning non-ASCII
      text, and sys.stdout captured. Asserts that raw_output (before JSON parsing) contains the
      literal Cyrillic and CJK characters, ensuring ensure_ascii=False on line 212 is actually
      exercised. A revert of that flag would now produce \uXXXX escapes and fail the assertion.

  - id: F-2
    title: "configure_windows_stdio() called after parser.parse_args() in mcp/dispatch.py"
    severity: low
    location: "mempalace_code/mcp/dispatch.py:174"
    claim: >
      In the MCP main() function, argparse.parse_args(argv) ran before configure_windows_stdio().
      On Windows, if argparse prints an error message to stderr (e.g. for an unrecognised flag),
      that write goes to the legacy-encoded stream. The CLI wires stdio correctly (before argparse);
      MCP was inconsistent.
    decision: fixed
    fix: >
      Moved the `from .._stdio import configure_windows_stdio` + `configure_windows_stdio()` block
      to before `args = parser.parse_args(argv)` in dispatch.main(), matching the CLI call order.

  - id: F-3
    title: "# pragma: win32 is not a registered coverage exclusion pragma"
    severity: info
    location: "mempalace_code/_stdio.py:31"
    claim: >
      coverage.py only recognises # pragma: no cover by default. # pragma: win32 is a custom
      pragma that requires a [tool.coverage.report] exclude_lines entry to take effect. No such
      entry exists in pyproject.toml, so the win32-only branch shows as uncovered on Linux/macOS
      CI runs. There is no current coverage gate in this project, so no job fails.
    decision: dismissed

  - id: F-4
    title: "RaisingStream.self.calls is an unused attribute"
    severity: info
    location: "tests/test_stdio.py:30"
    claim: >
      RaisingStream.__init__ initialises self.calls = [] but reconfigure() always raises and
      never appends to it. The attribute is never read in any assertion. Minor test-helper
      dead code.
    decision: dismissed

totals:
  fixed: 2
  backlogged: 0
  dismissed: 2

fixes_applied:
  - "Rewrote test_mcp_stdout_write_uses_ensure_ascii_false to call dispatch.main(argv=[]) via patched TOOLS and assert literal non-ASCII chars in raw stdout output"
  - "Moved configure_windows_stdio() call before parser.parse_args(argv) in mcp/dispatch.main() for consistent stdio-before-argparse ordering"

new_backlog: []
