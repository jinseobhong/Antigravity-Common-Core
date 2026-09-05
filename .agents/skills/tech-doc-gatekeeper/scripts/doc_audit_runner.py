#!/usr/bin/env python3
"""
Technical Documentation Quality Gatekeeper - Automated Static Scanner
Scans markdown technical documentation for:
1. Hard gates: Unresolved placeholders (TBD, TODO, Lorem Ipsum), secrets
2. Quality defects: Untyped code blocks, heading hierarchy skipping, weasel words, empty sections
Outputs JSON for agentic ingestion and formal text for humans.
"""

import sys
import os
import re
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ensure UTF-8 output on Windows console
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

DOC_EXTENSIONS = {".md", ".markdown", ".mdx"}

# 1. Hard Gate: Placeholders & Secrets
PLACEHOLDER_PATTERNS = [
    ("Unresolved TBD Marker", re.compile(r"(?i)\b(?:TBD|FIXME)\b")),
    ("Incomplete Placeholder Notice", re.compile(r"\[(?:작성 예정|여기에 설명 추가|설명 추가 예정|TODO)\]")),
    ("Lorem Ipsum Text Block", re.compile(r"(?i)\blorem\s+ipsum\b")),
]

SECRET_PATTERNS = [
    ("GitHub Personal Access Token", re.compile(r"ghp_[A-Za-z0-9_]{36}")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Slack API Token", re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}")),
    ("Private Key Block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

# 2. Quality Defects
WEASEL_WORDS = [
    ("Ambiguous Weasel Word (적절히)", re.compile(r"적절히\s+(?:설정|구현|처리|작성)")),
    ("Ambiguous Weasel Word (대략/대체로)", re.compile(r"(?:대략|대체로|보통은)\s+(?:동작|완료|실행)")),
    ("Ambiguous Weasel Word (알아서)", re.compile(r"알아서\s+(?:처리|판단|설정)")),
]


def scan_markdown(file_path: Path, root_path: Path) -> List[Dict[str, Any]]:
    findings = []
    rel_path = file_path.relative_to(root_path).as_posix()

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return findings

    in_code_block = False
    current_fence_length = 0
    last_heading_level = 0
    previous_line_was_heading = False
    previous_heading_line = 0

    for line_num, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        # Handle Code Blocks (CommonMark specification compliant)
        fence_match = re.match(r"^(`{3,})(.*)", line)
        if fence_match:
            backticks, rest = fence_match.groups()
            flen = len(backticks)
            if not in_code_block:
                in_code_block = True
                current_fence_length = flen
                lang_tag = rest.strip()
                if not lang_tag:
                    findings.append({
                        "category": "UNTYPED_CODE_BLOCK",
                        "severity": "HIGH",
                        "type": "Code block missing language identifier tag",
                        "file": rel_path,
                        "line": line_num,
                        "evidence": line[:80]
                    })
            else:
                if flen >= current_fence_length:
                    in_code_block = False
                    current_fence_length = 0
            previous_line_was_heading = False
            continue

        if in_code_block:
            # Check secrets inside code examples
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append({
                        "category": "HARD_GATE_SECRET",
                        "severity": "CRITICAL",
                        "type": name,
                        "file": rel_path,
                        "line": line_num,
                        "evidence": line[:80]
                    })
            continue

        # Check Headings & Hierarchy
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            current_level = len(heading_match.group(1))

            # Empty section check: previous line was heading and current is also heading
            if previous_line_was_heading:
                findings.append({
                    "category": "EMPTY_SECTION",
                    "severity": "MEDIUM",
                    "type": "Empty section detected without body content",
                    "file": rel_path,
                    "line": previous_heading_line,
                    "evidence": f"Heading level {last_heading_level} has no body text before next heading"
                })

            # Check skipped heading levels (e.g. H1 -> H3)
            if last_heading_level > 0 and (current_level - last_heading_level > 1):
                findings.append({
                    "category": "HEADING_HIERARCHY_VIOLATION",
                    "severity": "MEDIUM",
                    "type": f"Skipped heading level (H{last_heading_level} -> H{current_level})",
                    "file": rel_path,
                    "line": line_num,
                    "evidence": line[:80]
                })

            last_heading_level = current_level
            previous_line_was_heading = True
            previous_heading_line = line_num
            continue
        elif line:
            # Line has content, so section is not empty
            previous_line_was_heading = False

        # Check Placeholders (Outside code blocks & excluding inline backtick literals)
        line_without_inline_code = re.sub(r"`[^`]+`", "", line)
        for name, pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(line_without_inline_code):
                findings.append({
                    "category": "HARD_GATE_PLACEHOLDER",
                    "severity": "CRITICAL",
                    "type": name,
                    "file": rel_path,
                    "line": line_num,
                    "evidence": line[:80]
                })

        # Check Weasel Words
        for name, pattern in WEASEL_WORDS:
            if pattern.search(line_without_inline_code):
                findings.append({
                    "category": "WEASEL_WORD_AMBIGUITY",
                    "severity": "HIGH",
                    "type": name,
                    "file": rel_path,
                    "line": line_num,
                    "evidence": line[:80]
                })

    return findings


def get_git_changed_files(root_dir: Path) -> List[Path]:
    """Retrieve list of modified, staged, and newly added documentation files via Git."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(root_dir),
            capture_output=True,
            text=True,
            check=True
        )
        files = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                file_str = parts[1].strip('"')
                if "->" in file_str:
                    file_str = file_str.split("->")[1].strip().strip('"')
                p = (root_dir / file_str).resolve()
                if p.is_file() and p.suffix.lower() in DOC_EXTENSIONS:
                    files.append(p)
        return files
    except Exception:
        return []


def run_doc_audit(
    target_dir: Path,
    target_files: Optional[List[Path]] = None,
    use_diff: bool = False
) -> Dict[str, Any]:
    target_dir = target_dir.resolve()
    all_findings = []
    file_count = 0

    if use_diff:
        scanned_paths = get_git_changed_files(target_dir)
        scan_mode = "git_diff"
    elif target_files:
        scanned_paths = [Path(f).resolve() for f in target_files if Path(f).is_file()]
        scan_mode = "explicit_files"
    else:
        scanned_paths = []
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for file in files:
                p = Path(root) / file
                if p.suffix.lower() in DOC_EXTENSIONS:
                    scanned_paths.append(p)
        scan_mode = "directory_walk"

    for file_path in scanned_paths:
        if file_path.suffix.lower() not in DOC_EXTENSIONS:
            continue

        file_count += 1
        findings = scan_markdown(file_path, target_dir)
        all_findings.extend(findings)

    hard_gate_violation = any(f["severity"] == "CRITICAL" for f in all_findings)

    # Calculate Deductions
    deductions = 0
    for f in all_findings:
        if f["severity"] == "CRITICAL":
            deductions += 25
        elif f["severity"] == "HIGH":
            deductions += 10
        elif f["severity"] == "MEDIUM":
            deductions += 5

    prelim_score = max(0, 100 - deductions)
    verdict = "PASS" if (prelim_score >= 90 and not hard_gate_violation) else "HOLD"

    return {
        "status": "success",
        "scan_mode": scan_mode,
        "target_directory": str(target_dir),
        "hard_gate_violated": hard_gate_violation,
        "preliminary_score": prelim_score,
        "verdict": verdict,
        "documents_scanned": file_count,
        "total_defects": len(all_findings),
        "findings": all_findings
    }


def main():
    parser = argparse.ArgumentParser(description="Technical Documentation Quality Gatekeeper Scanner")
    parser.add_argument("--target-dir", type=str, default=".", help="Root workspace directory")
    parser.add_argument("--files", nargs="*", type=str, help="Specific file(s) to scan")
    parser.add_argument("--diff", action="store_true", help="Scan only Git modified and staged files")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    target_files = [Path(f) for f in args.files] if args.files else None
    results = run_doc_audit(Path(args.target_dir), target_files=target_files, use_diff=args.diff)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("=" * 65)
        print("🏛️ Technical Documentation Quality Scan Results")
        print("=" * 65)
        print(f"Target Directory : {results['target_directory']}")
        print(f"Documents Scanned: {results['documents_scanned']}")
        print(f"Hard Gate Status : {'🚨 VIOLATED (Hard Quality Gate Failure)' if results['hard_gate_violated'] else '✅ CLEAR'}")
        print(f"Quality Score    : {results['preliminary_score']} / 100")
        print(f"Review Verdict   : {'✅ PASS (Gate Cleared - Ready for User Review)' if results['verdict'] == 'PASS' else '🛑 HOLD (Remediation Required)'}")
        print(f"Defects Found    : {results['total_defects']}")
        print("-" * 65)

        if results["findings"]:
            print("Defects Detected for Remediation:")
            for idx, item in enumerate(results["findings"], 1):
                print(f"  [{idx}] [{item['severity']}] {item['type']} at {item['file']}:{item['line']}")
                print(f"      Text: {item['evidence']}")
        else:
            print("✅ All automated document criteria cleared. No defects detected.")
        print("=" * 65)

    if results["verdict"] == "HOLD":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
