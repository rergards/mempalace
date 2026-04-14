---
slug: MINE-EAGER-EMBED-INIT
goal: "Force eager embedding model init during 'Loading embedding model...' phase so all HuggingFace output appears before batch processing begins"
risk: low
risk_note: "Already implemented — plan documents the existing solution for pipeline bookkeeping"
files:
  - path: mempalace/miner.py
    change: "Already correct: collection.warmup() called at line 1488, between 'Loading embedding model...' and 'Model ready.' print statements"
  - path: mempalace/storage.py
    change: "Already correct: LanceStore.warmup() (line 600–602) calls self._embed(['warmup']); DrawerStore base has no-op warmup() stub"
  - path: tests/test_storage.py
    change: "Already correct: TestWarmup class (line 196–205) covers both embed-call delegation and no-crash behaviour"
  - path: tests/test_miner.py
    change: "Already correct: test_mine_calls_warmup_once (line 770–786) asserts warmup is called exactly once before batch processing"
acceptance:
  - id: AC-1
    when: "mine() runs on any project"
    then: "All HuggingFace model-loading output appears between 'Loading embedding model...' and 'Model ready.' — satisfied by collection.warmup() call at miner.py:1488"
  - id: AC-2
    when: "flush_batch() executes subsequent embedding batches"
    then: "No HuggingFace loading output appears — model is already warm from AC-1 warmup call"
  - id: AC-3
    when: "test_mine_calls_warmup_once runs"
    then: "Passes: asserts mock_store.warmup.assert_called_once()"
  - id: AC-4
    when: "TestWarmup.test_warmup_calls_embed runs"
    then: "Passes: asserts _embed is called with ['warmup']"
out_of_scope:
  - "ChromaDB legacy backend — ChromaStore.warmup() inherits the no-op base; ChromaDB loads its own model lazily and there is no equivalent forcing mechanism"
  - "convo_miner.py — does not call mine(); its embedding path is separate"
  - "MCP server path — add_drawer() calls upsert() which calls _embed(); server is long-lived so first request absorbs the load cost; not a UX issue"
---

## Design Notes

- **Already shipped**: The fix was implemented as part of commit `530688f` (task MINE-LANCE-COMPACT). No code changes are required.

- **How it works**: `LanceStore.__init__` calls `_get_embedder()` which registers the sentence-transformers function with LanceDB but does **not** load model weights (lazy). The first `_embed()` call triggers HuggingFace's `SentenceTransformer.__init__` which prints "Loading weights…" etc. `warmup()` in `mine()` forces this first call before any batch reaches `flush_batch()`.

- **Why the base class stub matters**: `DrawerStore.warmup()` is a docstring-only stub (returns `None`) rather than `@abstractmethod` so that ChromaStore and other future backends need not implement it. The `mine()` call is unconditional — safe for all backends.

- **Test coverage**: Both the unit path (`test_warmup_calls_embed` — verifies delegation) and the integration path (`test_mine_calls_warmup_once` — verifies call site) are covered. The integration test uses `patch("mempalace.miner.get_collection")` to avoid real model loading.
