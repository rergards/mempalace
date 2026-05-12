slug: MINE-RUBY-SMART
round: 1
date: 2026-05-12
commit_range: 5f596fc..HEAD
findings:
  - id: F-1
    title: "No test for predicate method suffix (def valid?)"
    severity: medium
    location: "tests/test_symbol_extract.py:616"
    claim: >
      The method pattern includes [!?=]? to capture predicate (?) and bang (!)
      suffixes — a feature explicitly named in the design notes as first-class.
      No test exercised the ? suffix, so a regression removing it from the
      pattern would pass all tests undetected.
    decision: fixed
    fix: "Added test_ruby_predicate_method asserting def valid? -> ('valid?', 'method')"

  - id: F-2
    title: "No test for bang method suffix (def save!)"
    severity: medium
    location: "tests/test_symbol_extract.py:616"
    claim: >
      Same gap as F-1 for the ! suffix. The bang suffix is distinct from
      the predicate suffix and warrants its own regression guard.
    decision: fixed
    fix: "Added test_ruby_bang_method asserting def save! -> ('save!', 'method')"

  - id: F-3
    title: "No test for plain attr pattern (attr :name, old-style)"
    severity: low
    location: "mempalace_code/mining/symbols.py:671"
    claim: >
      The _RB_EXTRACT list includes a fallback pattern for the old-style
      `attr :name` form (Ruby 1.x). The pattern is correct and distinct
      from attr_reader/writer/accessor (uses \b to prevent overlap), but
      it has no test. Low severity because the pattern is never exercised
      in modern Rails/Ruby code, but the untested path is a quality gap.
    decision: fixed
    fix: "Added test_ruby_plain_attr asserting attr :name -> ('name', 'attr')"

totals:
  fixed: 3
  backlogged: 0
  dismissed: 0

fixes_applied:
  - "Added test_ruby_predicate_method for def valid? -> ('valid?', 'method')"
  - "Added test_ruby_bang_method for def save! -> ('save!', 'method')"
  - "Added test_ruby_plain_attr for attr :name -> ('name', 'attr')"

new_backlog: []
