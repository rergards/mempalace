---
slug: STORE-CHROMA-DELETE-WING-LIMIT
goal: "Replace direct self._col.get() call in ChromaStore.delete_wing with self.get() so the limit=10000 wrapper applies"
risk: low
risk_note: "One-line change in a deprecated backend; existing test_delete_wing already covers this path"
files:
  - path: mempalace/_chroma_store.py
    change: "Line 86: replace `self._col.get(where={\"wing\": wing})` with `self.get(where={\"wing\": wing})`"
acceptance:
  - id: AC-1
    when: "The fix is applied"
    then: "Change is exactly 1 line (replacing self._col.get with self.get)"
  - id: AC-2
    when: "`pytest tests/test_storage.py -x -q` is run"
    then: "Existing test_delete_wing (and all delete_wing tests) pass without modification"
  - id: AC-3
    when: "`ruff check mempalace/_chroma_store.py` is run"
    then: "No lint errors"
out_of_scope:
  - "Any changes to LanceStore (not affected by this bug)"
  - "New tests — existing coverage is sufficient"
  - "ChromaDB deprecation or removal"
---

## Design Notes

- `ChromaStore.get()` (line 56) adds `limit=10000` as a default before delegating to `self._col.get()`. Without it, ChromaDB's own default page size (100) silently truncates results, meaning `delete_wing` would only delete the first 100 drawers in a wing larger than that.
- `self.get()` returns the same dict structure as `self._col.get()` — keys `ids`, `documents`, `metadatas`, etc. — so the `results.get("ids", [])` call on line 87 is unaffected.
- No need to change the `self._col.delete(ids=ids)` call on line 90; only the fetch path needs fixing.
- The `self.get()` wrapper does not add `include` or filtering side effects that could break the returned `ids` list.
