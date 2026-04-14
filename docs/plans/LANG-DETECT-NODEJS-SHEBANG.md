---
slug: LANG-DETECT-NODEJS-SHEBANG
goal: "Extend node shebang pattern to match 'nodejs' (Debian/Ubuntu binary name)"
risk: low
risk_note: "Single-character regex change; no logic restructuring; existing tests remain valid"
files:
  - path: mempalace/miner.py
    change: "Change re.compile(r\"node\") to re.compile(r\"nodejs?\") in SHEBANG_PATTERNS"
  - path: tests/test_lang_detect.py
    change: "Add two parametrized shebang cases: #!/usr/bin/nodejs and #!/usr/bin/env nodejs"
acceptance:
  - id: AC-1
    when: "detect_language(Path('script'), '#!/usr/bin/nodejs\\n') is called"
    then: "returns 'javascript'"
  - id: AC-2
    when: "detect_language(Path('script'), '#!/usr/bin/env nodejs\\n') is called"
    then: "returns 'javascript'"
  - id: AC-3
    when: "existing 'node' shebang cases (#!/usr/bin/node, #!/usr/bin/env node) are tested"
    then: "still return 'javascript' (no regression)"
out_of_scope:
  - "Other interpreter aliases (e.g. node18, node20 versioned binaries)"
  - "Changes to extension-based detection"
  - "Any other SHEBANG_PATTERNS entries"
---

## Design Notes

- `fullmatch` is used on the extracted interpreter basename, so `r"nodejs?"` matches exactly `"node"` or `"nodejs"` — nothing else. No unintended broadening.
- The `?` quantifier makes `s` optional: `r"nodejs?"` → matches `"node"` (s absent) and `"nodejs"` (s present).
- Two new parametrized entries in `test_shebang_detection` are sufficient; no separate test function needed.
- No other patterns in `SHEBANG_PATTERNS` need changes for this task.
