---
slug: MINE-PHP
goal: "Add PHP (.php) language support to the code miner with regex-based symbol extraction for classes, interfaces, traits, enums, functions, and namespaces"
risk: low
risk_note: "Follows established pattern — identical to how Swift, Kotlin, C#, Java were added. No existing code changes, only additions."
files:
  - path: mempalace/miner.py
    change: "Add .php to EXTENSION_LANG_MAP and READABLE_EXTENSIONS; add PHP_BOUNDARY regex; add php to get_boundary_pattern() mapping; add _PHP_EXTRACT pattern list; add php to _LANG_EXTRACT_MAP; add php to chunk_file() dispatch tuple"
  - path: mempalace/searcher.py
    change: "Add 'php' to SUPPORTED_LANGUAGES; add 'trait' and 'namespace' to VALID_SYMBOL_TYPES"
  - path: mempalace/mcp_server.py
    change: "Add 'php' to mempalace_code_search language description string; add 'trait', 'namespace' to symbol_type description string"
  - path: tests/test_symbol_extract.py
    change: "Add PHP extract_symbol unit tests: class, abstract class, interface, trait, enum (PHP 8.1), function, namespace, typed method with attributes, access modifiers, no-match cases"
  - path: tests/test_miner.py
    change: "Add test_mine_php_roundtrip — full mine() cycle on .php files (proves file walker discovers .php via READABLE_EXTENSIONS and stored metadata has language='php', correct symbol_type/symbol_name)"
  - path: tests/test_searcher.py
    change: "Add test_code_search_php_language — verify code_search(language='php') does not raise validation error; add test_code_search_trait_namespace_symbol_types — verify 'trait' and 'namespace' are accepted"
acceptance:
  - id: AC-1
    when: "A .php file containing `class UserService { ... }` is mined"
    then: "At least one drawer has language='php', symbol_type='class', symbol_name='UserService'"
  - id: AC-2
    when: "A .php file containing `interface Cacheable { ... }` is mined"
    then: "Drawer has symbol_type='interface', symbol_name='Cacheable'"
  - id: AC-3
    when: "A .php file containing `trait Loggable { ... }` is mined"
    then: "Drawer has symbol_type='trait', symbol_name='Loggable'"
  - id: AC-4
    when: "A .php file containing `namespace App\\Services;` is mined"
    then: "Drawer has symbol_type='namespace', symbol_name='App\\Services'"
  - id: AC-5
    when: "A .php file containing `enum Status: string { ... }` (PHP 8.1 backed enum) is mined"
    then: "Drawer has symbol_type='enum', symbol_name='Status'"
  - id: AC-6
    when: "A .php file containing `function processOrder(Order $order): Result { ... }` is mined"
    then: "Drawer has symbol_type='function', symbol_name='processOrder'"
  - id: AC-7
    when: "A .php file containing `abstract class BaseController { ... }` is mined"
    then: "Drawer has symbol_type='class', symbol_name='BaseController'"
  - id: AC-8
    when: "extract_symbol is called with a chunk containing only `$name = 'test';` (a variable assignment)"
    then: "Returns ('', '') — variable assignments are not extracted as symbols"
  - id: AC-9
    when: "A .php file with `#[Route('/api')]` attribute before a class is mined"
    then: "The attribute line is included in the class chunk (not orphaned in the preceding chunk)"
out_of_scope:
  - "Tree-sitter AST parsing for PHP"
  - "WordPress-specific constructs (hooks, filters, actions) — these are function calls, not declarations"
  - "Heredoc/nowdoc boundary detection within functions"
  - "Composer manifest parsing (composer.json is already handled as JSON)"
  - "Anonymous classes or closures — only named declarations are extracted"
---

## Design Notes

- **Regex-only, no tree-sitter.** PHP joins the Java/Kotlin/C#/Swift regex tier.

- **PHP access/declaration modifiers:** `public`, `private`, `protected`, `static`, `abstract`, `final`, `readonly` (PHP 8.1+). The boundary and extract patterns must handle arbitrary prefix chains of these.

- **Pattern ordering in `_PHP_EXTRACT`:**
  1. `namespace` first — must capture before other patterns match (namespace declarations are standalone lines with no braces sometimes)
  2. `interface` before `class` (a class can implement an interface, avoid matching `class` in `interface` context)
  3. `trait` before `class` (similarly a distinct declaration type)
  4. `abstract class` and `final class` are just `class` with modifiers — the class pattern handles them via optional modifier prefix
  5. `enum` (PHP 8.1) — `enum Foo: string { ... }` with optional backing type
  6. `function` last — standalone functions and methods both use `function` keyword

- **PHP_BOUNDARY regex structure:**
  ```
  ^(?:(?:abstract|final|readonly)\s+)*(?:class|interface|trait|enum)\s+\w+
  |^namespace\s+[\w\\]+
  |^(?:(?:public|private|protected|static|abstract|final)\s+)*function\s+\w+
  ```

- **PHP 8.1+ attributes (`#[...]`):** PHP uses `#[Attribute]` syntax (not `@` like Java/Swift). Extend `comment_prefixes` with `"#["` when `canonical == "php"` so attribute lines attach to their declaration chunk. Standard `//` and `/*` comments are already covered.

- **Namespace extraction:** PHP namespaces use backslash separators (`App\Http\Controllers`). The extract pattern capture group should be `([\w\\]+)` rather than `(\w+)` to capture the full qualified namespace.

- **`trait` and `namespace` as symbol types:** These are PHP-specific (trait) and general (namespace) concepts not yet in VALID_SYMBOL_TYPES. Both are meaningful search filters — users searching a Laravel project will want to filter by trait to find Eloquent mixins, and namespace to understand code organization.

- **READABLE_EXTENSIONS:** Add `.php` to the set so the file walker picks up PHP files.

- **No `comment_prefixes` for PHP docblocks:** PHP uses `/** ... */` for docblocks, which is already covered by existing prefixes (`"/**"`, `"/*"`, `"*"`, `"*/"`). Only `#[` needs special handling.
