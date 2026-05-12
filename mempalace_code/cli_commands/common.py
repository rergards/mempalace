"""Shared helpers used by multiple CLI command modules."""


def parse_include_ignored(raw_list) -> list:
    """Flatten comma-separated include-ignored paths into a clean list."""
    result = []
    for raw in raw_list or []:
        result.extend(part.strip() for part in raw.split(",") if part.strip())
    return result


def fmt_bytes(n: int | float) -> str:
    """Human-readable byte count."""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n = n / 1024
    return f"{n:.1f} TB"
