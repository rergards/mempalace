slug: MINE-K8S
round: 1
date: 2026-04-21
commit_range: c09e7b8..3ba21b7
findings:
  - id: F-1
    title: "Dead code: _K8S_DETECT_RE compiled but never used"
    severity: low
    location: "mempalace/miner.py:757"
    claim: >
      _K8S_DETECT_RE was compiled at module level but _is_k8s_manifest uses two
      separate re.search calls instead. The regex was dead weight that could mislead
      future readers into thinking the proximity-match logic was active.
    decision: fixed
    fix: "Removed the unused _K8S_DETECT_RE compile block (lines 757-760)."

  - id: F-2
    title: "Large K8s documents split by adaptive_merge_split lose kind/name in sub-chunks"
    severity: medium
    location: "mempalace/miner.py:1354"
    claim: >
      _chunk_k8s_manifest passes each YAML document to adaptive_merge_split as a
      single-element list. When the document exceeds HARD_MAX (4000 chars) — e.g. a
      large ConfigMap or CRD spec — adaptive_merge_split calls _split_oversized,
      producing multiple sub-chunks. Sub-chunks past the first do not contain kind:
      or metadata.name:, so _extract_k8s_symbol returns ("", "") for them, producing
      empty symbol_type and symbol_name in the index for those chunks.
    decision: backlogged
    backlog_slug: MINE-K8S-LARGE-DOC

  - id: F-3
    title: "--- inside YAML block scalar values triggers false document splits"
    severity: medium
    location: "mempalace/miner.py:1356"
    claim: >
      The split regex (?:^|\n)---\s*(?:\n|$) matches any --- at a line boundary,
      including --- inside YAML block scalars (| or > style) used in ConfigMap/Secret
      data fields. A ConfigMap that embeds a config file or script containing --- on
      its own line would be incorrectly split into multiple documents, corrupting chunk
      boundaries and metadata.
    decision: backlogged
    backlog_slug: MINE-K8S-YAML-SEPARATOR

totals:
  fixed: 1
  backlogged: 2
  dismissed: 0

fixes_applied:
  - "Removed dead _K8S_DETECT_RE regex (miner.py) — 5 lines of unused code deleted."

new_backlog:
  - slug: MINE-K8S-LARGE-DOC
    summary: "Propagate kind+name from first sub-chunk to all sub-chunks of large K8s documents"
  - slug: MINE-K8S-YAML-SEPARATOR
    summary: "Guard _chunk_k8s_manifest against splitting on --- inside YAML block scalar values"
