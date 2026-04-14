---
slug: MINE-DEVOPS-INFRA
goal: "Make miner scan, detect, and chunk DevOps/infrastructure files (Terraform, Docker, Helm, Ansible, Make, etc.)"
risk: low
risk_note: "Additive — only new entries in existing data structures and one new code path for filename-based detection. No changes to existing chunking or storage logic."
files:
  - path: mempalace/miner.py
    change: "Add DevOps extensions to EXTENSION_LANG_MAP and READABLE_EXTENSIONS; add FILENAME_LANG_MAP and KNOWN_FILENAMES for extensionless files (Dockerfile, Makefile, Vagrantfile); add .terraform to SKIP_DIRS; update detect_language() with filename fallback; update scan_project() to accept known extensionless filenames; add HCL_BOUNDARY and route terraform/hcl through chunk_code(); update get_boundary_pattern() and chunk_file() dispatch"
  - path: mempalace/searcher.py
    change: "Add new DevOps language strings to SUPPORTED_LANGUAGES: terraform, hcl, dockerfile, make, gotemplate, jinja2, conf, ini"
  - path: mempalace/mcp_server.py
    change: "Update code_search tool description to list the new DevOps language filter values"
  - path: tests/test_lang_detect.py
    change: "Add language detection tests for .tf, .hcl, Dockerfile, Makefile, .tpl, .j2, .conf/.cfg/.ini, Vagrantfile"
  - path: tests/test_chunking.py
    change: "Add HCL boundary chunking test for multi-resource .tf file"
  - path: tests/test_miner.py
    change: "Add scan_project integration tests for Terraform, Dockerfile, Makefile inclusion and .terraform/ skip"
  - path: tests/test_mcp_server.py
    change: "Add test verifying new DevOps languages appear in supported_languages hint list"
acceptance:
  - id: AC-1
    when: "A project contains .tf, .tfvars, .hcl files"
    then: "scan_project() returns them; detect_language() returns 'terraform' or 'hcl'; drawers are stored with correct language metadata"
  - id: AC-2
    when: "A project contains a file named Dockerfile (no extension)"
    then: "scan_project() returns it; detect_language() returns 'dockerfile'; drawers are stored with language='dockerfile'"
  - id: AC-3
    when: "A project contains a file named Makefile or GNUmakefile (no extension)"
    then: "scan_project() returns it; detect_language() returns 'make'; drawers are stored with language='make'"
  - id: AC-4
    when: "A project contains .tpl (Helm) or .j2/.jinja2 (Ansible) files"
    then: "scan_project() returns them; detect_language() returns 'gotemplate' or 'jinja2'; drawers are stored with correct language metadata"
  - id: AC-5
    when: "A project contains .conf, .cfg, or .ini files"
    then: "scan_project() returns them; detect_language() returns 'conf' or 'ini'; drawers are stored with correct language metadata"
  - id: AC-6
    when: "A project contains a .terraform/ directory"
    then: "scan_project() skips the entire directory (SKIP_DIRS)"
  - id: AC-7
    when: "A .tf file with multiple resource/variable/output blocks is mined"
    then: "chunk_code() splits at HCL block boundaries; each resource/variable/output starts a new chunk"
  - id: AC-8
    when: "Existing tests are run after the changes"
    then: "All existing tests pass unchanged (no regressions)"
out_of_scope:
  - "Tree-sitter AST chunking for HCL/Terraform (regex boundaries are sufficient for v1)"
  - "Symbol extraction for DevOps languages (extract_symbol returns empty for non-programming languages)"
  - "Dockerfile or Makefile structural boundary patterns (adaptive_lines is adequate; HCL is the priority)"
  - "New room auto-detection keywords for infrastructure files (users configure rooms in mempalace.yaml)"
  - ".env files (security risk — may contain secrets)"
  - "Jenkinsfile → groovy mapping (groovy is not an infrastructure language in scope; defer to a future task)"
  - "README language-support table update (docs-only follow-up after merge)"
---

## Design Notes

### Extension and filename maps

New entries in **EXTENSION_LANG_MAP**:

| Extension(s)     | Language string |
|------------------|-----------------|
| `.tf`, `.tfvars` | `"terraform"`   |
| `.hcl`           | `"hcl"`         |
| `.tpl`           | `"gotemplate"`  |
| `.j2`, `.jinja2` | `"jinja2"`      |
| `.conf`, `.cfg`  | `"conf"`        |
| `.ini`           | `"ini"`         |
| `.mk`            | `"make"`        |

New **FILENAME_LANG_MAP** dict (for extensionless files):

| Filename         | Language string |
|------------------|-----------------|
| `Dockerfile`     | `"dockerfile"`  |
| `Containerfile`  | `"dockerfile"`  |
| `Makefile`       | `"make"`        |
| `GNUmakefile`    | `"make"`        |
| `Vagrantfile`    | `"ruby"`        |

Derive `KNOWN_FILENAMES = set(FILENAME_LANG_MAP.keys())` for use in `scan_project()`.

### READABLE_EXTENSIONS

Add all new extensions from EXTENSION_LANG_MAP to READABLE_EXTENSIONS so `scan_project()` picks them up.

### SKIP_DIRS

Add `".terraform"` — this directory contains downloaded provider plugins and can be hundreds of MB. Similar to `node_modules`.

### scan_project() change

In the inner filename loop (around line 1447), after the extension check, also allow files whose `filename` is in `KNOWN_FILENAMES`:

```python
if filepath.suffix.lower() not in READABLE_EXTENSIONS and not exact_force_include:
    if filename not in KNOWN_FILENAMES:
        continue
```

### detect_language() change

After extension lookup fails and before shebang fallback, check `filepath.name` against `FILENAME_LANG_MAP`:

```python
if filepath.name in FILENAME_LANG_MAP:
    return FILENAME_LANG_MAP[filepath.name]
```

### HCL boundary pattern

Terraform/HCL files have clear top-level block structure. Add a regex boundary:

```python
HCL_BOUNDARY = re.compile(
    r"^(?:resource|data|module|variable|output|locals|provider|terraform)\s+",
    re.MULTILINE,
)
```

Wire it into `get_boundary_pattern()` for `"terraform"` and `"hcl"`, and add both languages to the `chunk_code()` dispatch in `chunk_file()`.

### Chunking strategy for other DevOps files

- **Dockerfile, Makefile, Helm templates, Jinja2, config files** — All route through `chunk_adaptive_lines()` via the `else` branch in `chunk_file()`. This is adequate: these files are typically small and don't benefit from structural boundary detection in v1.
- **Terraform/HCL** — Route through `chunk_code()` with `HCL_BOUNDARY` for meaningful resource-level chunks. This is the highest-value addition since .tf files can be large with many resource blocks.

### Downstream search / API surface

The miner emits new `language` values that must also be accepted by the code-search API, otherwise users can mine these files but cannot filter for them.

**searcher.py** — add to `SUPPORTED_LANGUAGES` (around line 157):

```python
# devops / infrastructure
"terraform",
"hcl",
"dockerfile",
"make",
"gotemplate",
"jinja2",
"conf",
"ini",
```

`ruby` is already present (covers `Vagrantfile`). `groovy` is out of scope (see out_of_scope).

**mcp_server.py** — update the `code_search` tool's `language` field description (around line 652) to include the new values so MCP clients see them in the schema.

**tests/test_mcp_server.py** — extend `test_code_search_invalid_language` (or add a sibling test) to assert the new DevOps languages appear in the `supported_languages` hint list returned on invalid-language errors.

### Test plan

**tests/test_lang_detect.py** — language detection (pure function tests):
- `test_detect_language_terraform` — `.tf` → `"terraform"`
- `test_detect_language_dockerfile` — `Dockerfile` → `"dockerfile"`
- `test_detect_language_makefile` — `Makefile` → `"make"`
- `test_detect_language_helm_template` — `.tpl` → `"gotemplate"`
- `test_detect_language_jinja2` — `.j2` → `"jinja2"`
- `test_detect_language_config` — `.conf`/`.cfg`/`.ini` → correct language
- `test_detect_language_vagrantfile` — `Vagrantfile` → `"ruby"`

**tests/test_chunking.py** — HCL boundary chunking:
- `test_chunk_terraform_hcl_boundaries` — multi-resource `.tf` file splits at resource boundaries

**tests/test_miner.py** — scan_project integration (temp dirs):
- `test_scan_project_includes_terraform_files` — `.tf` files appear in scan results
- `test_scan_project_includes_dockerfile` — extensionless `Dockerfile` appears
- `test_scan_project_includes_makefile` — extensionless `Makefile` appears
- `test_scan_project_skips_terraform_dir` — `.terraform/` is skipped

**tests/test_mcp_server.py** — API surface:
- `test_code_search_devops_languages_in_hint` — new DevOps languages appear in `supported_languages` list

**Verification command:**
```bash
python -m pytest tests/test_lang_detect.py tests/test_chunking.py tests/test_miner.py tests/test_mcp_server.py -q
```
