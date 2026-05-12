slug: REFAC-MINER-MODULES
phase: polish
date: 2026-05-12
commit_range: a7723d1..HEAD
reverted: false
findings:
  - id: P-1
    title: "Redundant elif for terraform/hcl in chunk_file dispatcher"
    category: structural
    location: "mempalace_code/mining/chunkers.py:419"
    evidence: |
      elif language in ("terraform", "hcl"):
          return chunk_code(content, language, source_file)
      The preceding `if` block also calls `chunk_code(content, language, source_file)`
      with an identical call — the elif adds no distinct behavior.
    decision: fixed
    fix: "Added 'terraform' and 'hcl' to the main if-tuple; removed the redundant elif branch."

  - id: P-2
    title: "Pass-body if-block with restating comment in skip_optimize guard"
    category: verbal
    location: "mempalace_code/mining/orchestrator.py:496"
    evidence: |
      if skip_optimize:
          pass  # caller will optimize later
      elif config.optimize_after_mine:
          ...
      else:
          ...
      Comment restates what `pass` already means; the pass-body structure hides the
      real condition behind a no-op arm.
    decision: fixed
    fix: "Inverted to `if not skip_optimize:` and nested the optimize/else arms inside it."

  - id: P-3
    title: "Redundant ternary `csproj_room_map if csproj_room_map else None` (×2)"
    category: volume
    location: "mempalace_code/mining/orchestrator.py:371,417"
    evidence: |
      csproj_room_map=csproj_room_map if csproj_room_map else None,
      Downstream callees (detect_room, _collect_specs_for_file) guard with
      `if csproj_room_map:`, which treats {} and None identically. The conditional
      expression converts {} to None unnecessarily.
    decision: fixed
    fix: "Replaced both occurrences with `csproj_room_map=csproj_room_map`."

totals:
  fixed: 3
  dismissed: 0

fixes_applied:
  - "chunkers.py: folded terraform/hcl into the main chunk_code if-tuple, removed duplicate elif"
  - "orchestrator.py: replaced `if skip_optimize: pass` with `if not skip_optimize:` and nested body"
  - "orchestrator.py: removed two `x if x else None` redundant ternaries for csproj_room_map"
