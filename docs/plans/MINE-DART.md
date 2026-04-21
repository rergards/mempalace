---
slug: MINE-DART
goal: "Add Dart (.dart) language support to the code miner with regex-based symbol extraction for classes, mixins, extensions, enums, typedefs, factory constructors, and top-level functions"
risk: low
risk_note: "Additive change only, follows the Scala/Swift/PHP regex-tier template. No tree-sitter grammar required; no edits to existing language code paths."
files:
  - path: mempalace/miner.py
    change: "Add .dart to EXTENSION_LANG_MAP (→ 'dart') and READABLE_EXTENSIONS; add DART_BOUNDARY regex; register 'dart'/.dart in get_boundary_pattern(); add _DART_EXTRACT pattern list (mixin, extension_type, extension, enum, typedef, sealed/final/base/interface class, class, factory constructor, top-level function); add 'dart' to _LANG_EXTRACT_MAP; add 'dart' to the chunk_file() code-language tuple; extend comment_prefixes with '@' for 'dart' in chunk_code() (Dart annotations: @override, @deprecated, @pragma) and reuse the _SWIFT_PURE_ATTR guard so `@override void foo()` single-line annotation+decl is handled like Swift/Scala"
  - path: mempalace/searcher.py
    change: "Add 'dart' to SUPPORTED_LANGUAGES; add 'mixin', 'extension_type', 'constructor' to VALID_SYMBOL_TYPES (class, extension, enum, typedef/type, function already exist)"
  - path: mempalace/mcp_server.py
    change: "Add 'dart' to the mempalace_code_search language description string; add 'mixin', 'extension_type', 'constructor' to the symbol_type description string"
  - path: tests/test_symbol_extract.py
    change: "Add Dart extract_symbol unit tests: class, abstract class, sealed class (Dart 3), final/base/interface class (Dart 3 class modifiers), mixin, mixin class, extension (named), extension type (Dart 3.3+), enum (plain), enhanced enum with methods, typedef (function type alias), top-level function (sync, async, expression-body `=>`, generic `<T>`), factory constructor (bare and named `factory Foo.fromJson`), named constructor inside class body (`Foo.named()`), no-match for bare `var x = 1` / `final y = 2` property lines, no-match for annotation-only lines (@override alone)"
  - path: tests/test_miner.py
    change: "Add test_mine_dart_roundtrip — full mine() cycle on a Flutter-style project with multiple .dart files (widget class extending StatelessWidget, mixin, extension, enum, factory constructor, async function). Verify walker discovers .dart via READABLE_EXTENSIONS and stored drawers have language='dart' with expected symbol_name/symbol_type values (covers AC-1, AC-2, AC-3, AC-4, AC-8, AC-9)"
  - path: tests/test_chunking.py
    change: "Add test_chunk_code_dart_annotation_attachment — direct chunk_code(..., 'dart', ...) verifying @override / @deprecated / @pragma lines attach to the following declaration (mirrors existing Swift/Scala annotation coverage); add test_chunk_code_dart_async_function — verify `Future<User> fetchUser() async { ... }` becomes its own chunk (async keyword doesn't break detection); add test_chunk_file_dart_routing — verify chunk_file() routes .dart through chunk_code() not adaptive fallback"
  - path: tests/test_lang_detect.py
    change: "Add `.dart` to the extension parametrize list in test_extension_detection mapping to 'dart'"
  - path: tests/test_searcher.py
    change: "Add test_code_search_dart_language — code_search(language='dart') does not raise validation error; add test_code_search_dart_invalid_language_hint — when code_search is called with an invalid language, the error response's supported_languages list includes 'dart'; add test_code_search_new_symbol_types_dart — 'mixin', 'extension_type', 'constructor' accepted as symbol_type filters"
acceptance:
  - id: AC-1
    when: "A .dart file containing `class UserService { ... }` is mined"
    then: "At least one drawer has language='dart', symbol_type='class', symbol_name='UserService'"
  - id: AC-2
    when: "A .dart file containing `mixin Serializable { String toJson(); }` is mined"
    then: "Drawer has symbol_type='mixin', symbol_name='Serializable'"
  - id: AC-3
    when: "A .dart file containing `extension StringX on String { bool get isBlank => trim().isEmpty; }` is mined"
    then: "Drawer has symbol_type='extension', symbol_name='StringX'"
  - id: AC-4
    when: "A .dart file containing `enum Color { red, green, blue }` is mined"
    then: "Drawer has symbol_type='enum', symbol_name='Color'"
  - id: AC-5
    when: "extract_symbol is called on `sealed class Shape {}` (Dart 3 class modifier)"
    then: "Returns ('Shape', 'class') — sealed/base/final/interface prefixes do not break extraction"
  - id: AC-6
    when: "extract_symbol is called on `extension type UserId(int value) {}` (Dart 3.3+)"
    then: "Returns ('UserId', 'extension_type') — extension type is NOT collapsed to 'extension'"
  - id: AC-7
    when: "extract_symbol is called on `typedef Json = Map<String, dynamic>;`"
    then: "Returns ('Json', 'type')"
  - id: AC-8
    when: "A .dart file containing `Future<User> fetchUser(int id) async { ... }` is mined"
    then: "Drawer has symbol_type='function', symbol_name='fetchUser' (async keyword preserved in content, not broken as boundary)"
  - id: AC-9
    when: "A .dart file containing a class with `factory User.fromJson(Map<String, dynamic> json) { ... }` is mined"
    then: "A drawer exists with symbol_type='constructor' and symbol_name containing 'fromJson' (bare or qualified as 'User.fromJson')"
  - id: AC-10
    when: "extract_symbol is called on `  var count = 0;` (a field inside a class body, indented)"
    then: "Returns ('', '') — field/variable declarations are not extracted as symbols"
  - id: AC-11
    when: "A .dart file with `@override\\nvoid dispose() { ... }` is mined"
    then: "The resulting chunk for `dispose` contains the `@override` annotation line (annotation not orphaned into the preceding chunk)"
  - id: AC-12
    when: "code_search is called with language='dart'"
    then: "Does not return a validation error (language is in SUPPORTED_LANGUAGES)"
  - id: AC-13
    when: "code_search is called with symbol_type='mixin' (or 'extension_type', or 'constructor')"
    then: "Does not return a validation error (symbol_types are in VALID_SYMBOL_TYPES)"
  - id: AC-14
    when: "detect_language is called on a file named `widget.dart`"
    then: "Returns 'dart'"
out_of_scope:
  - "Tree-sitter AST parsing for Dart — no tree_sitter_dart grammar is installed in the Python ecosystem; regex tier only (matches Kotlin/Swift/PHP/Scala)"
  - "Flutter-specific widget tree analysis or `build()` method body parsing — treated as ordinary class/method chunks"
  - "Part files (`part of`) / library aliases / deferred imports — no special handling; they land in preamble chunks"
  - "Getter/setter-only boundaries (`String get name => ...`, `set name(String v) { ... }`) — too ambiguous with getters used as expression-body properties; defer until user demand"
  - "Operator overloads (`operator +`) — rare; not a primary search target"
  - "Regular (non-factory) constructors inside class bodies unless they appear via the named-constructor pattern `ClassName.named()` — the default unnamed constructor `ClassName()` is indistinguishable from a method call without AST and is intentionally NOT extracted"
  - "Dart build-runner generated files (`.g.dart`, `.freezed.dart`) are mined as regular .dart; no content-aware filtering"
  - "`pubspec.yaml` / `analysis_options.yaml` — already handled by the existing yaml chunker; nothing new here"
---

## Design Notes

- **Regex-only, no tree-sitter.** No `tree_sitter_dart` exists in the Python ecosystem. Dart joins the Kotlin/Swift/PHP/Scala regex tier.

- **Single extension:** `.dart`. No worksheet/script variant to worry about (unlike Scala's `.sc`).

- **Dart 3 class modifiers** (`base`, `final`, `interface`, `sealed`, `mixin class`): all handled as prefix modifiers in the class arm. Pattern tolerates arbitrary modifier chains. Note: `final class` in Dart is distinct from a `final` field — the regex only fires when `class` follows.

- **Pattern ordering (strict):**
  1. `extension type` before plain `extension` (Dart 3.3+ feature; the word `type` is the disambiguator).
  2. `mixin class` before plain `class` (also before `mixin`) — `mixin` here is a modifier on `class`, not the noun.
  3. `mixin` (standalone) before `class`.
  4. `typedef` — anchored at line start, safe against in-body usage.
  5. `enum` — anchor keyword disjoint from others; order flexible.
  6. `class` last among type declarations.
  7. `factory <Name>(` — anchored factory constructor; placed before the generic function arm so the return type of a factory is not misread as a top-level function.
  8. Top-level function arm last — it's the loosest pattern.

- **Top-level function detection** uses a constrained return-type-then-name-then-paren shape:
  ```
  ^(?:@\w+(?:\([^)]*\))?\s+)*
  (?:(?:external|static|abstract)\s+)*
  (?:void|Future(?:<[^>]*>)?|Stream(?:<[^>]*>)?|[A-Z]\w*(?:<[^>]*>)?|[a-z]\w*(?:<[^>]*>)?)\s+
  (\w+)\s*(?:<[^>]*>)?\s*\(
  ```
  The identifier-capture group deliberately requires a type token first to avoid matching expression statements like `someVar(x)` or `print(foo);`. This is the Kotlin/Java approach adapted — `fun`/`public` anchors are absent in Dart, so we must infer via return type. A rare false positive on `MyFunc something(args)` at top level is acceptable (it IS a function declaration if it compiles).

- **Method extraction inside class bodies is deferred.** Dart methods lack a leading keyword (no `fun`/`def`/`func`), so reliably distinguishing a method declaration from a method call without AST is hard. Decision: only top-level functions and `factory`/named constructors are boundaries inside code. Methods inside classes are part of the surrounding class chunk (same behavior as bare Java methods under regex tier when no access modifier is present, in the absence of explicit modifiers).

- **Named constructors (`ClassName.named()`)** inside a class body ARE extractable when `extract_symbol` receives a chunk beginning with that line. Pattern: `^\s*(?:const\s+)?(\w+)\.(\w+)\s*\(` where the first `\w+` equals a known class name — since we can't know the class at this layer, we capture the qualified name `ClassName.named` as the symbol_name and emit `symbol_type='constructor'`. If ambiguous (method call `foo.bar()`), we require the line to NOT end with a `;` and to be followed by `{` or `=>` or a parameter list initializer (`:`), which a statement would not be. Keep the pattern conservative; accept that some named constructors may not extract cleanly (they still land in the class chunk — not lost).

- **Factory constructors** use `factory` as the unique anchor: `^\s*(?:const\s+)?factory\s+(\w+)(?:\.\w+)?`. Captures `ClassName` or `ClassName.named` — emit `symbol_type='constructor'`.

- **Async/await** is a suffix modifier on function signatures, NOT a boundary keyword. The top-level function regex must match signatures that END with `async`/`async*`/`sync*` before `{` or `=>`. Simpler: anchor on `(` — the async modifier appears after the `)`, so the current pattern (which anchors on return-type + name + `(`) is already tolerant. AC-8 explicitly verifies this.

- **Annotation attachment (`@`):** Dart uses `@override`, `@deprecated`, `@immutable`, `@pragma('vm:entry-point')`, `@Deprecated('use X')`. Mirror the Swift/Scala handling: extend `comment_prefixes` with `"@"` for `canonical == "dart"` in `chunk_code()`, and reuse the existing `_SWIFT_PURE_ATTR` (or an aliased `_DART_PURE_ATTR = _SWIFT_PURE_ATTR`) in the pure-attribute guard at miner.py:1913-1919 so a pure `@override`-only line attaches while `@Deprecated('x') var y = 0` on a non-boundary field does not get swallowed. No regex duplication — reuse the shared pattern by adding `"dart"` to the `canonical in ("swift", "scala")` tuple there.

- **Boundary regex sketch (unified):**
  ```
  ^(?:@\w+(?:\([^)]*\))?\s+)*
  (?:
      (?:(?:abstract|base|final|interface|sealed|mixin)\s+)*extension\s+type\s+\w+
    | (?:(?:abstract|base|final|interface|sealed|mixin)\s+)*extension\s+\w+
    | (?:(?:abstract|base|final|interface|sealed|mixin)\s+)+class\s+\w+
    | (?:(?:abstract|base|final|interface|sealed)\s+)*class\s+\w+
    | (?:base\s+)?mixin\s+\w+
    | enum\s+\w+
    | typedef\s+\w+
    | (?:const\s+)?factory\s+\w+(?:\.\w+)?\s*\(
    | (?:@\w+(?:\([^)]*\))?\s+)*(?:(?:external|static)\s+)*[\w<>?\[\],. ]+?\s+\w+\s*(?:<[^>]*>)?\s*\(
  )
  ```
  Keep the class and mixin-class arms separate so `mixin class Foo` is matched before a plain `class` arm might swallow it.

- **Symbol types emitted:**
  - New: `mixin`, `extension_type`, `constructor`.
  - Reused: `class`, `extension`, `enum`, `type` (for typedef), `function`.
  - `VALID_SYMBOL_TYPES` additions: `mixin`, `extension_type`, `constructor`. `class`, `extension`, `enum`, `type`, `function` already exist.

- **No boundary for `var`/`final`/`const` field declarations.** Same rationale as Kotlin `val`/`var`, Swift `let`/`var`, Scala `val`/`var`. Keeps chunk noise low.

- **`library`, `import`, `export`, `part`, `part of` directives** are not boundaries. They live in the preamble chunk.

- **Integration test uses `mine()`, not just `process_file()`** — proves `.dart` is in `READABLE_EXTENSIONS` and the file walker picks it up end-to-end. Single `test_mine_dart_roundtrip` covers multiple constructs in separate files (one class, one mixin, one extension, one enum, one factory-constructor class, one async top-level function) to verify the ACs through the full pipeline.

- **Direct `chunk_code` coverage for annotations and async** in `tests/test_chunking.py` catches regressions earlier than integration layer — shorter signal, no palace/embedding machinery.

## Resolved Decisions

- **`mixin` is a first-class symbol type (not flattened to `class`).** Rationale: in Dart a mixin is a distinct language construct — it cannot be constructed, has specific `on` clauses, and users searching Dart/Flutter codebases filter on it (common in state-management patterns). Mirrors the Scala `trait` / Kotlin `sealed_class` precedent.

- **`extension_type` is a first-class symbol type, distinct from `extension`.** Dart 3.3 extension types have different semantics (zero-cost wrappers with static dispatch) versus regular extensions (method injection). Conflating them would make search results misleading. Cost is one extra VALID_SYMBOL_TYPES entry.

- **`constructor` is a shared symbol type for factory and named constructors.** Rather than inventing `factory_constructor` + `named_constructor` and forcing callers to know Dart internals, a single `constructor` covers both. The `symbol_name` preserves the specific form (`User.fromJson` for named, `User` for bare factory on class User). Matches how Python/Kotlin represent constructors implicitly.

- **`typedef` emits `symbol_type='type'`.** Consistent with Scala `type` alias and Swift `typealias` — callers searching `symbol_type=type` across languages get consistent results. No new value needed.

- **Default (unnamed) constructors are NOT extracted.** A bare `MyClass() : x = 0 {}` inside the class body is indistinguishable from a method call without context. Including it would require class-name tracking, which pushes into AST territory. Named/factory constructors are sufficient for the task's acceptance criteria.

- **Getter/setter boundaries are deferred.** `String get name => _name;` and `set name(String v) { _name = v; }` are valid top-level or class-member boundaries in theory, but the `get`/`set` keywords collide with method invocations in statement position. Defer until concrete user demand — mentioned explicitly in `out_of_scope` so the decision is discoverable.

- **`searcher.py` and `mcp_server.py` are in scope.** Without updating `SUPPORTED_LANGUAGES` / `VALID_SYMBOL_TYPES`, `code_search(language="dart", symbol_type="mixin")` would reject valid Dart queries. MCP description strings are updated so client hints match backend validation — same rationale as MINE-SCALA.
