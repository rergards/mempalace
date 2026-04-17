slug: MINE-DOTNET
round: 1
date: 2026-04-17
commit_range: d6ad53c..HEAD
findings:
  - id: F-1
    title: "TargetFrameworks (plural) silently dropped — no triples emitted for multi-target projects"
    severity: high
    location: "mempalace/miner.py:1961"
    claim: |
      parse_dotnet_project_file() only matched the singular <TargetFramework> element.
      Modern .NET SDK projects that target multiple runtimes use the plural element:

        <TargetFrameworks>net8.0;net6.0;netstandard2.0</TargetFrameworks>

      This is a semicolon-delimited string. The parser treated it like an unknown tag
      and silently produced no "targets_framework" triples. A project exclusively using
      <TargetFrameworks> appeared to have no known target — a silent data loss bug.

      Reproduction:
        csproj with <TargetFrameworks>net8.0;net6.0</TargetFrameworks>
        parse_dotnet_project_file(path) → [] (no targets_framework triples)
    decision: fixed
    fix: |
      Added an elif branch for tag == "TargetFrameworks" immediately after the
      TargetFramework branch. It splits the element text on ";" and emits one
      ("project", "targets_framework", fw) triple per non-empty token.

      Added two regression tests in tests/test_dotnet_config.py:
        - test_parse_csproj_multi_target_frameworks: verifies all three targets appear
        - test_parse_csproj_multi_target_no_singular_duplicate: verifies exactly 3
          triples with predicate "targets_framework" (no phantom singular entry)

  - id: F-2
    title: "'bin' in SKIP_DIRS is too broad — silently skips non-.NET script directories"
    severity: medium
    location: "mempalace/miner.py:155"
    claim: |
      MINE-DOTNET added 'bin', 'obj', and '.vs' to SKIP_DIRS. The '.vs' and 'obj'
      entries are unambiguously .NET-specific. However, 'bin' is widely used as a
      script/executable directory in other ecosystems:
        - Ruby on Rails: bin/rails, bin/rake, bin/bundle (Ruby source)
        - Go projects: bin/ directory for compiled output that may contain shell wrappers
        - Generic CLIs: many tools place executable scripts under bin/

      Mining a Ruby on Rails project with this version will silently skip all files
      under bin/, losing potentially useful Ruby source from the palace.

      The 'obj' entry is fine — no other ecosystem uses 'obj/' for source.
    decision: backlogged
    backlog_slug: MINE-BIN-SKIP-DIRS

  - id: F-3
    title: "No test for 'bin/'/'obj/' skip behavior on non-.NET projects"
    severity: low
    location: "tests/test_miner.py"
    claim: |
      test_skip_dirs_dotnet() in test_miner.py correctly verifies that .vs/, bin/, and
      obj/ are skipped on a .NET project layout. However, there is no test confirming
      that a non-.NET project with a legitimate bin/ directory (e.g. a Ruby on Rails
      project) would have those files skipped — making it harder to detect a regression
      if F-2 is ever addressed. This finding is subordinate to F-2 and will be resolved
      when F-2 is addressed.
    decision: backlogged
    backlog_slug: MINE-BIN-SKIP-DIRS

  - id: F-4
    title: "KnowledgeGraph always uses global path — no isolation for project-specific triples"
    severity: info
    location: "mempalace/cli.py:153"
    claim: |
      cmd_mine() instantiates KnowledgeGraph() with no db_path, so all .NET project
      triples (package refs, framework targets, project deps) accumulate in the global
      ~/.mempalace/knowledge_graph.sqlite3. Mining two different projects will mix
      their triples in the same store, which could be confusing when querying.

      This is consistent with the existing MemPalace design (all vectors also go into
      one palace, partitioned by wing). The KG store has no wing-level filtering today,
      but the source_file column allows post-hoc filtering. Not an implementation error,
      but worth tracking as a UX consideration.
    decision: dismissed

totals:
  fixed: 1
  backlogged: 2
  dismissed: 1
fixes_applied:
  - "parse_dotnet_project_file: handle <TargetFrameworks> (plural) by splitting on ';' and emitting one triple per target"
  - "tests/test_dotnet_config.py: add test_parse_csproj_multi_target_frameworks and test_parse_csproj_multi_target_no_singular_duplicate"
new_backlog:
  - slug: MINE-BIN-SKIP-DIRS
    summary: "'bin' in SKIP_DIRS silently excludes non-.NET script directories (Ruby on Rails, Go)"
