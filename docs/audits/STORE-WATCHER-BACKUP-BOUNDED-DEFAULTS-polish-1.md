slug: STORE-WATCHER-BACKUP-BOUNDED-DEFAULTS
phase: polish
date: 2026-05-12
commit_range: 76064a7..623eb43
reverted: false
findings:
  - id: P-1
    title: "Unreachable TypeError in _backup_retain_count_explicit except clause"
    category: defensive
    location: "mempalace_code/config.py:209"
    evidence: "except (TypeError, ValueError): — env_val is a str at this point (os.environ returns str, is not None already checked), so int(str) never raises TypeError"
    decision: dismissed
    reason: "Follows the established local style throughout config.py — backup_retain_count (:190), backup_min_free_bytes (:236), and others all use except (TypeError, ValueError) for int() conversions. Fixing only this instance would be inconsistent with the file's convention."
totals:
  fixed: 0
  dismissed: 1
fixes_applied: []
