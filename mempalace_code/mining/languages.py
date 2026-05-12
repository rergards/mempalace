"""mining.languages — Language detection for mined files."""

import re
from pathlib import Path

from ..language_catalog import (
    extension_language_map,
    filename_language_map,
    shebang_patterns,
)

EXTENSION_LANG_MAP = extension_language_map()
FILENAME_LANG_MAP = filename_language_map()
SHEBANG_PATTERNS = list(shebang_patterns())

_HELM_VALUES_NAME_RE = re.compile(r"^values.*\.ya?ml$")


def _is_helm_chart_file(filepath) -> bool:
    """Return True if filepath is part of a Helm chart (path-context detection).

    Chart.yaml is always Helm. values*.yaml requires Chart.yaml in the same directory.
    Files under a templates/ directory require Chart.yaml in the templates/ parent.
    """
    p = Path(filepath)
    name = p.name

    if name == "Chart.yaml":
        return True

    ext = p.suffix.lower()
    if ext not in (".yaml", ".yml", ".tpl"):
        return False

    # values*.yaml: Chart.yaml must be in the same directory (chart root)
    if _HELM_VALUES_NAME_RE.match(name):
        return (p.parent / "Chart.yaml").is_file()

    # Template files: walk up to find a directory named "templates"; its parent is the chart root
    current = p.parent
    while True:
        if current.name == "templates":
            return (current.parent / "Chart.yaml").is_file()
        parent = current.parent
        if parent == current:
            break
        current = parent

    return False


def _is_k8s_manifest(content: str) -> bool:
    """Return True if content looks like a Kubernetes manifest (has both apiVersion: and kind: lines)."""
    return bool(
        re.search(r"^apiVersion:\s", content, re.MULTILINE)
        and re.search(r"^kind:\s", content, re.MULTILINE)
    )


def detect_language(filepath, content: str = "") -> str:
    """
    Detect the programming language for a file.

    Resolution order:
    1. File extension lookup via EXTENSION_LANG_MAP.
    2. Filename lookup via FILENAME_LANG_MAP (for extensionless files like Dockerfile, Makefile).
    3. Shebang inspection on the first line (for extensionless files).
    4. Content-based K8s detection: YAML files with apiVersion+kind become 'kubernetes'.
    5. Returns "unknown" if neither matches.
    """
    ext = filepath.suffix.lower()
    lang = None
    if ext in EXTENSION_LANG_MAP:
        lang = EXTENSION_LANG_MAP[ext]
    elif filepath.name in FILENAME_LANG_MAP:
        lang = FILENAME_LANG_MAP[filepath.name]
    else:
        # Shebang fallback — only for files with no recognized extension
        first_line = content.split("\n")[0] if content else ""
        if first_line.startswith("#!"):
            parts = first_line[2:].strip().split()
            if parts:
                basename = parts[0].split("/")[-1]
                if basename == "env" and len(parts) > 1:
                    interp = parts[1].split("/")[-1]
                else:
                    interp = basename
                for pattern, interp_lang in SHEBANG_PATTERNS:
                    if pattern.fullmatch(interp):
                        lang = interp_lang
                        break

    if lang is None:
        return "unknown"

    # Helm override: chart-context files take precedence over YAML and gotemplate detection
    if lang in ("yaml", "gotemplate") and _is_helm_chart_file(filepath):
        return "helm"

    # Content-based K8s override: YAML files that are K8s manifests
    if lang == "yaml" and content and _is_k8s_manifest(content):
        return "kubernetes"

    return lang
