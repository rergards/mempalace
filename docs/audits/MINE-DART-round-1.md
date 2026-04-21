slug: MINE-DART
round: 1
date: 2026-04-21
commit_range: 18632c1..HEAD
findings:
  - id: F-1
    title: "DART_BOUNDARY factory arm misses generic factory constructors — factory Cls<T>(...)"
    severity: medium
    location: "mempalace/miner.py:755"
    claim: >
      The factory arm in DART_BOUNDARY used `factory\s+\w+(?:\.\w+)?\s*\(` which requires
      `(` immediately after the constructor name (or named suffix). When a factory constructor
      carries generic type parameters — `factory Cache<K, V>(Config config)` — the `<K, V>`
      sits between the name and `(`, so the pattern returned no match. As a result, the factory
      line was never recorded as a structural boundary, the factory body was folded into the
      surrounding class-body chunk, and `extract_symbol` could not emit `symbol_type='constructor'`
      for that factory. The corresponding `_DART_EXTRACT` factory pattern already handled this
      correctly via `[(<]`, creating a silent inconsistency between boundary detection and
      symbol extraction.
    decision: fixed
    fix: >
      Added `(?:<[^>]*>)?` between the name group and `\s*\(` in the DART_BOUNDARY factory arm:
      `r"|(?:const\s+)?factory\s+\w+(?:\.\w+)?\s*(?:<[^>]*>)?\s*\("`.
      Added regression test `test_chunk_code_dart_generic_factory_boundary` in
      tests/test_chunking.py that verifies `factory Repository<T>.fromConfig(Config config)`
      becomes its own chunk.

  - id: F-2
    title: "Plain mixin extraction pattern would capture 'class' as name for 'mixin class' input if used in isolation"
    severity: info
    location: "mempalace/miner.py:1459"
    claim: >
      The `mixin` entry in `_DART_EXTRACT` uses `r"^...(?:base\s+)?mixin\s+(\w+)\b"`.
      For input `"mixin class Observable {}"`, this pattern's `(\w+)` would greedily capture
      `class` as the symbol name — an incorrect result. In practice this never fires because
      the `mixin class` pattern (index 2 in `_DART_EXTRACT`) is checked before the plain
      `mixin` pattern (index 3), so `extract_symbol` always returns `("Observable", "class")`
      via ordering protection. The risk surfaces only if the pattern is called in isolation
      outside `extract_symbol`.
    decision: dismissed
    fix: ""

  - id: F-3
    title: "Nullable return types (String?, User?, int?) not detected as function boundaries or extracted"
    severity: medium
    location: "mempalace/miner.py:762 and mempalace/miner.py:1509"
    claim: >
      Both DART_BOUNDARY's typed function arm and _DART_EXTRACT's function pattern require
      `\s+` (whitespace) immediately after the return type token. Dart null-safety syntax
      appends `?` to make types nullable — `String?`, `User?`, `int?`, `List<String>?` — with
      no whitespace between the type and the `?`. As a result, `String? getName()`,
      `User? findUser(int id)`, `int? getCount()` and all other nullable-typed top-level
      functions were silently skipped: no chunk boundary was created and no drawer was emitted
      with `symbol_type='function'`. Since Dart 2.12 (2021) null-safety is opt-in and since
      Dart 3.0 (2023) it is mandatory, so this affects the majority of real-world Flutter/Dart
      codebases. `Future<User?>` was unaffected because the `?` sits inside the angle brackets
      and is consumed by `[^>]*`.
    decision: fixed
    fix: >
      Added `\??` between the return type group and `\s+` in both DART_BOUNDARY (miner.py:762)
      and the `_DART_EXTRACT` function pattern (miner.py:1509):
      `r"...(?:void|int|...|[A-Z]\w*(?:<[^>]*>)?)\??\s+(\w+)..."`.
      Added four regression tests in tests/test_symbol_extract.py
      (test_dart_nullable_return_type_string, test_dart_nullable_return_type_uppercase,
      test_dart_nullable_return_type_primitive, test_dart_nullable_return_type_generic) and
      one boundary test in tests/test_chunking.py
      (test_chunk_code_dart_nullable_return_type).

  - id: F-4
    title: "test_chunking.py fails ruff format check"
    severity: low
    location: "tests/test_chunking.py"
    claim: >
      The new Dart test additions in tests/test_chunking.py did not conform to ruff's
      formatting rules. `ruff format --check mempalace/ tests/` reported 1 file needing
      reformatting. This would cause CI format gates to fail.
    decision: fixed
    fix: "Ran `ruff format tests/test_chunking.py` to auto-format the file."

  - id: F-5
    title: "Annotation with ')' inside string arg not recognized as pure-attr or boundary prefix"
    severity: low
    location: "mempalace/miner.py:692 (_SWIFT_PURE_ATTR) and mempalace/miner.py:739 (DART_BOUNDARY)"
    claim: >
      Both `_SWIFT_PURE_ATTR` and `DART_BOUNDARY`'s annotation prefix use `[^)]*` to match
      annotation arguments, which stops at the first `)` and fails when `)` appears inside
      a string literal in the argument (e.g. `@pragma('vm:(entry-point)')`). Two consequences:
      (1) `@pragma('vm:(entry-point)') class Cache {}` on a single line is not recognized as
      a structural boundary; (2) `@pragma('vm:(entry-point)')` on its own line before a
      declaration fails `_SWIFT_PURE_ATTR` and is not attached to the following chunk.
      Impact is limited: `@pragma('vm:entry-point')` (the common form, no nested parens)
      works correctly; `@override`, `@deprecated`, `@immutable` (no argument parens) are
      unaffected; putting annotation+declaration on the same line is non-standard Dart style;
      declarations still mine correctly even without the annotation attached.
    decision: dismissed
    fix: ""

  - id: F-6
    title: "DART_BOUNDARY factory arm wrong group ordering — factory Cls<T>.named(...) still not a boundary after F-1 fix; test assertion too weak to catch it"
    severity: medium
    location: "mempalace/miner.py:755 and tests/test_chunking.py:test_chunk_code_dart_generic_factory_boundary"
    claim: >
      The F-1 fix placed the generic type param group AFTER the named constructor suffix:
      `factory\s+\w+(?:\.\w+)?\s*(?:<[^>]*>)?\s*\(`. For `factory Repository<T>.fromConfig(Config config)`,
      `(?:\.\w+)?` tries `.fromConfig` but next char is `<` so it skips; then `(?:<[^>]*>)?` matches
      `<T>`; then `\(` tries to match `.` in `.fromConfig(` and fails. Result: the boundary is never
      detected, and the factory folds into the class body chunk. The test for F-1 used exactly this
      `ClassName<T>.named(...)` form but only asserted that SOME chunk contained `fromConfig` (which is
      trivially true since the class chunk always contains the factory body). The factory form without
      named suffix (`factory Cache<K,V>(cfg)`) IS correctly handled by the F-1 fix.
    decision: fixed
    fix: >
      Changed group ordering in DART_BOUNDARY's factory arm from
      `factory\s+\w+(?:\.\w+)?\s*(?:<[^>]*>)?\s*\(` to
      `factory\s+\w+(?:<[^>]*>)?(?:\.\w+)?\s*\(` — generic params now come BEFORE the named suffix.
      This handles all four factory forms: bare `factory Foo()`, named `factory Foo.from()`,
      generic `factory Foo<T>()`, and generic+named `factory Foo<T>.from()`.
      Also strengthened `test_chunk_code_dart_generic_factory_boundary` to assert the factory chunk
      does NOT start with `class` — verifying it is a separate chunk, not the class body chunk.

totals:
  fixed: 4
  backlogged: 0
  dismissed: 2

fixes_applied:
  - "DART_BOUNDARY factory arm: added (?:<[^>]*>)? to handle generic type params before '(' (miner.py:755)"
  - "Added test_chunk_code_dart_generic_factory_boundary in tests/test_chunking.py"
  - "DART_BOUNDARY + _DART_EXTRACT function arm: added \\?? after return type to handle nullable types like String?, User?, int? (miner.py:762, miner.py:1509)"
  - "Added 4 symbol-extract tests and 1 chunking test for nullable return types"
  - "Ran ruff format on tests/test_chunking.py to fix formatting violations (F-4)"
  - "DART_BOUNDARY factory arm: swapped group ordering to (?:<[^>]*>)?(?:\\.\\w+)? so ClassName<T>.named(...) forms are detected as boundaries (miner.py:755); strengthened F-1 regression test assertion (tests/test_chunking.py)"

new_backlog: []
