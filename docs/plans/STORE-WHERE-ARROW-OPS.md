---
slug: STORE-WHERE-ARROW-OPS
goal: "Fix _where_to_arrow_mask to handle $gt/$gte/$lt/$lte/$ne/$eq operator dicts via pyarrow.compute"
risk: low
risk_note: "Isolated static method with no side effects; only adds a new elif branch to existing loop"
files:
  - path: mempalace/storage.py
    change: "Add operator-dict branch in _where_to_arrow_mask (lines ~580-593) to map $gt/$gte/$lt/$lte/$ne/$eq to pc.greater/pc.greater_equal/pc.less/pc.less_equal/pc.not_equal/pc.equal"
  - path: tests/test_storage_lance.py
    change: "Add TestIterAll tests for $gt, $lte, $ne operator dicts on int32 chunk_index; also cover $gte/$lt/$eq for completeness"
acceptance:
  - id: AC-1
    when: "iter_all(where={'chunk_index': {'$gt': 1}}) is called on a store with rows having chunk_index 0, 1, 2"
    then: "Returns only the row with chunk_index=2"
  - id: AC-2
    when: "iter_all(where={'chunk_index': {'$lte': 1}}) is called on the same store"
    then: "Returns rows with chunk_index 0 and 1 only"
  - id: AC-3
    when: "iter_all(where={'chunk_index': {'$ne': 1}}) is called"
    then: "Returns rows with chunk_index 0 and 2, excluding chunk_index=1"
  - id: AC-4
    when: "iter_all(where={'wing': 'alpha'}) is called (existing string equality)"
    then: "Still returns only alpha rows — no regression"
  - id: AC-5
    when: "ruff check mempalace/ tests/ is run"
    then: "No lint errors"
out_of_scope:
  - "$in operator (already supported in _where_to_sql but not required by this task)"
  - "String comparison operators ($gt on string columns)"
  - "Changes to _where_to_sql"
  - "ChromaStore / legacy Chroma backend"
---

## Design Notes

- The fix is a single `elif isinstance(value, dict):` block inside the `for key, value in where.items()` loop in `_where_to_arrow_mask` (storage.py ~line 583).
- Operator→pc-function mapping:
  - `$eq`  → `pc.equal`
  - `$ne`  → `pc.not_equal`
  - `$gt`  → `pc.greater`
  - `$gte` → `pc.greater_equal`
  - `$lt`  → `pc.less`
  - `$lte` → `pc.less_equal`
- Unknown ops (e.g. `$in`) are silently skipped within the dict — matches `_where_to_sql` behavior for unknown ops.
- `chunk_index` is stored as `int32`; pyarrow.compute comparisons against Python `int` scalars work natively (Arrow casts automatically). Float columns (also in `_META_FIELD_SPEC`) work the same way.
- Do NOT add `$in` here — it requires `pc.is_in` with a `ValueSet` array and the empty-list edge case; out of scope per task constraints.
- Test fixture: add 3 drawers with explicit `chunk_index` metadata (0, 1, 2) to `TestIterAll` tests; verify row counts and values.
- All new tests go into `tests/test_storage_lance.py` in the existing `TestIterAll` class to keep AC-3 compliant.
