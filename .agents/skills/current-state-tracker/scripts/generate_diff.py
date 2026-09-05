#!/usr/bin/env python3
"""
Sandbox Diff Generator - Pre-Promotion Diff Inspector
Compares files in ./sandbox/ against the project root to generate clean unified diffs.
Enables the user to review all changes before promoting sandbox deliverables to production.
Supports summary output, unified diffs, and patch file generation.
"""

import sys
import os
import difflib
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# Windows console UTF-8 support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

IGNORED_DIRS = {
    ".git", ".svn", "node_modules", "venv", ".venv", "env",
    "__pycache__", ".pytest_cache", "dist", "build", "coverage"
}

IGNORED_FILES = {
    ".DS_Store", "thumbs.db"
}


def read_file_lines(file_path: Path) -> List[str]:
    """Safely read lines from a file with UTF-8 encoding (newlines stripped)."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().splitlines()
    except (OSError, UnicodeDecodeError):
        return []


def compare_single_file(sandbox_file: Path, root_file: Path, rel_path: str) -> Tuple[str, List[str]]:
    """Compare sandbox file against root file and return status and diff lines."""
    sb_lines = read_file_lines(sandbox_file)
    if not root_file.exists():
        diff = list(difflib.unified_diff(
            [], sb_lines,
            fromfile="/dev/null",
            tofile=f"b/{rel_path}",
            lineterm=""
        ))
        return "NEW", diff

    root_lines = read_file_lines(root_file)
    if sb_lines == root_lines:
        return "IDENTICAL", []

    diff = list(difflib.unified_diff(
        root_lines, sb_lines,
        fromfile=f"a/{rel_path}",
        tofile=f"b/{rel_path}",
        lineterm=""
    ))
    return "MODIFIED", diff


class SandboxDiffInspector:
    def __init__(self, sandbox_dir: Path, root_dir: Path):
        self.sandbox_dir = sandbox_dir.resolve()
        self.root_dir = root_dir.resolve()
        self.results: Dict[str, List[Tuple[str, List[str]]]] = {
            "NEW": [],
            "MODIFIED": [],
            "IDENTICAL": []
        }

    def scan(self, filter_file: str = None):
        """Scan all files in sandbox and compare against root."""
        for root, dirs, files in os.walk(self.sandbox_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for file in files:
                if file in IGNORED_FILES:
                    continue

                sb_path = Path(root) / file
                rel_path = sb_path.relative_to(self.sandbox_dir).as_posix()

                if filter_file and filter_file not in rel_path:
                    continue

                rt_path = self.root_dir / rel_path
                status, diff = compare_single_file(sb_path, rt_path, rel_path)
                self.results[status].append((rel_path, diff))


def format_report(inspector: SandboxDiffInspector, show_diffs: bool = True) -> str:
    """Format human-readable diff inspection report."""
    output = []
    output.append("=" * 65)
    output.append("🔍 [Sandbox to Production Diff Inspection Report]")
    output.append("=" * 65)
    output.append(f"• Sandbox Staging: {inspector.sandbox_dir}")
    output.append(f"• Target Root    : {inspector.root_dir}")
    output.append("-" * 65)

    n_new = len(inspector.results["NEW"])
    n_mod = len(inspector.results["MODIFIED"])
    n_same = len(inspector.results["IDENTICAL"])

    output.append(f"📊 Diff Summary: NEW={n_new} | MODIFIED={n_mod} | UNCHANGED={n_same}")
    output.append("-" * 65)

    if n_new == 0 and n_mod == 0:
        output.append("✅ Zero Diff: Sandbox and Production are completely identical.")
        output.append("=" * 65)
        return "\n".join(output)

    if inspector.results["NEW"]:
        output.append("📦 Newly Added in Sandbox (Staged for Promotion):")
        for rel_path, _ in inspector.results["NEW"]:
            output.append(f"  + [NEW] {rel_path}")

    if inspector.results["MODIFIED"]:
        output.append("📝 Modified in Sandbox (Pending User Review):")
        for rel_path, _ in inspector.results["MODIFIED"]:
            output.append(f"  * [MOD] {rel_path}")

    if show_diffs:
        output.append("\n" + "=" * 65)
        output.append("📜 Detailed Unified Diffs:")
        output.append("=" * 65)

        for rel_path, diff_lines in inspector.results["MODIFIED"]:
            output.append(f"\n--- [DIFF] {rel_path} ---")
            output.extend(diff_lines)

        for rel_path, diff_lines in inspector.results["NEW"]:
            output.append(f"\n+++ [NEW FILE] {rel_path} +++")
            output.extend(diff_lines[:30])
            if len(diff_lines) > 30:
                output.append(f"... ({len(diff_lines) - 30} more lines truncated)")

    output.append("=" * 65)
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Staging Sandbox to Production Diff Inspector")
    parser.add_argument("--sandbox-dir", type=str, default="./sandbox", help="Staging sandbox directory (default: ./sandbox)")
    parser.add_argument("--root-dir", type=str, default=".", help="Production workspace root directory (default: .)")
    parser.add_argument("--file", type=str, default=None, help="Filter specific file path")
    parser.add_argument("--summary", action="store_true", help="Only show high-level summary without line diffs")
    parser.add_argument("--output-patch", type=str, default=None, help="Write full patch file to destination")
    args = parser.parse_args()

    inspector = SandboxDiffInspector(Path(args.sandbox_dir), Path(args.root_dir))
    inspector.scan(filter_file=args.file)

    report_text = format_report(inspector, show_diffs=not args.summary)
    sys.stdout.write(report_text + "\n")
    sys.stdout.flush()

    if args.output_patch:
        patch_path = Path(args.output_patch)
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        patch_lines = []
        for _, diff in inspector.results["MODIFIED"]:
            patch_lines.extend(diff)
        for _, diff in inspector.results["NEW"]:
            patch_lines.extend(diff)
        with open(patch_path, "w", encoding="utf-8") as f:
            f.write("\n".join(patch_lines) + "\n")
        sys.stdout.write(f"\n[SUCCESS] Patch file saved to: {patch_path}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
