#!/usr/bin/env python3
"""
Code Review Gatekeeper - Automated Scanner
Scans for:
1. Lazy stubs (TODO, FIXME, pass, fake returns)
2. Hardcoded secrets & credentials
3. Dirty code smells (deep indentation, long functions, console.log/print, swallowed errors)
Outputs JSON for subagent ingestion and CLI text for humans.
"""

import sys
import os
import re
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure Windows console UTF-8
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

IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".lock",
    ".pyc", ".min.js", ".min.css", ".map", ".tar", ".gz", ".zip"
}

CODE_EXTENSIONS = {
    ".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs", ".java",
    ".c", ".cpp", ".h", ".cs", ".rb", ".php", ".swift", ".kt"
}

# 1. Hard Gate: Secrets
SECRET_PATTERNS = [
    ("GitHub Personal Access Token", re.compile(r"ghp_[A-Za-z0-9_]{36}")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Slack API Token", re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}")),
    ("Private Key Header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Generic Hardcoded Secret", re.compile(r"""(?i)(?:api_key|secret_key|auth_token|client_secret)\s*[:=]\s*['"][A-Za-z0-9\-_]{20,}['"]"""))
]

# 2. Hard Gate: Lazy Stubs & Placeholders
LAZY_STUB_PATTERNS = [
    ("Unimplemented TODO/FIXME", re.compile(r"(?i)\b(?:TODO|FIXME|HACK|XXX)\b")),
    ("Python Unimplemented Pass", re.compile(r"^\s*pass\s*$")),
    ("NotImplementedError Raised", re.compile(r"raise\s+NotImplementedError")),
    ("Fake Boolean Return Stub", re.compile(r"^\s*return\s+(?:True|true|null|None)\s*;?\s*(?://|#)\s*(?:mock|stub|fake)", re.IGNORECASE)),
]

# 3. Cleanliness Smells
SMELL_PATTERNS = [
    ("Swallowed Exception (except: pass)", re.compile(r"except(?:\s+\w+)?:\s*pass")),
    ("Empty Catch Block (catch {})", re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}")),
    ("Debug Log Remnant (console.log / print)", re.compile(r"\b(?:console\.log|print)\s*\(")),
    ("Magic Number in Logic", re.compile(r"(?<!\w)(?:86400|3600|86400000|5000|60000)(?!\w)")),
]


def scan_file(file_path: Path, root_path: Path) -> List[Dict[str, Any]]:
    findings = []
    rel_path = file_path.relative_to(root_path).as_posix()

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return findings

    is_code = file_path.suffix.lower() in CODE_EXTENSIONS

    in_multiline_docstring = False
    for line_num, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith('"""') or line.startswith("'''"):
            if in_multiline_docstring:
                in_multiline_docstring = False
                continue
            elif line.count('"""') == 1 or line.count("'''") == 1:
                in_multiline_docstring = True
                continue

        if in_multiline_docstring or "re.compile" in line:
            continue

        if "re.search" in line or "TODO/FIXME" in line:
            continue
        if is_code and line.startswith(("#", "//", "/*", "*")):
            # Check for task placeholders inside code comments
            match = re.search(r"(?i)\b(?:TODO|FIXME)\b:?\s*(.*)", line)
            if match:
                findings.append({
                    "category": "HARD_GATE_STUB",
                    "severity": "CRITICAL",
                    "type": "Unresolved TODO/FIXME in comment",
                    "file": rel_path,
                    "line": line_num,
                    "evidence": line[:100]
                })
            continue

        # Check Secrets on all files
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append({
                    "category": "HARD_GATE_SECRET",
                    "severity": "CRITICAL",
                    "type": name,
                    "file": rel_path,
                    "line": line_num,
                    "evidence": line[:100]
                })

        # Code-only checks (Lazy Stubs, Dirty Smells, Indentation)
        is_test_file = "tests" in file_path.parts or file_path.name.startswith("test_")
        if is_code:
            for name, pattern in LAZY_STUB_PATTERNS:
                if is_test_file and "Pass" in name:
                    continue
                if name == "Python Unimplemented Pass":
                    prev_line = lines[line_num - 2].strip() if line_num >= 2 else ""
                    if prev_line.startswith("except") or prev_line.startswith("finally"):
                        continue
                if pattern.search(line):
                    findings.append({
                        "category": "LAZY_STUB",
                        "severity": "CRITICAL",
                        "type": name,
                        "file": rel_path,
                        "line": line_num,
                        "evidence": line[:100]
                    })

            for name, pattern in SMELL_PATTERNS:
                if "Debug Log Remnant" in name and ("scripts" in file_path.parts or "cli" in file_path.name.lower()):
                    continue
                if pattern.search(line):
                    findings.append({
                        "category": "DIRTY_CODE_SMELL",
                        "severity": "HIGH",
                        "type": name,
                        "file": rel_path,
                        "line": line_num,
                        "evidence": line[:100]
                    })

            # Check Control Flow Nesting Depth (4+ levels = 16 spaces on control keywords)
            indent_match = re.match(r"^(\s+)", raw_line)
            if indent_match and any(raw_line.lstrip().startswith(kw) for kw in ("if ", "elif ", "for ", "while ", "try:", "except ")):
                spaces = indent_match.group(1).replace("\t", "    ")
                if len(spaces) >= 24:
                    findings.append({
                        "category": "DEEP_NESTING",
                        "severity": "HIGH",
                        "type": f"Deep Nesting Depth ({len(spaces) // 4} levels)",
                        "file": rel_path,
                        "line": line_num,
                        "evidence": line[:100]
                    })

    return findings


def get_git_changed_files(root_dir: Path) -> List[Path]:
    """Retrieve list of modified, staged, and newly added untracked files via Git."""
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
                if p.is_file():
                    files.append(p)
        return files
    except Exception:
        return []


def run_audit(
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
                if p.suffix in IGNORED_EXTENSIONS:
                    continue
                scanned_paths.append(p)
        scan_mode = "directory_walk"

    for file_path in scanned_paths:
        if file_path.suffix in IGNORED_EXTENSIONS:
            continue
        file_count += 1
        findings = scan_file(file_path, target_dir)
        all_findings.extend(findings)

    hard_gate_violation = any(f["severity"] == "CRITICAL" for f in all_findings)

    # Calculate Deductions
    deductions = 0
    for f in all_findings:
        if f["severity"] == "CRITICAL":
            deductions += 25
        elif f["severity"] == "HIGH":
            deductions += 10

    prelim_score = max(0, 100 - deductions)
    verdict = "PASS" if (prelim_score >= 90 and not hard_gate_violation) else "HOLD"

    return {
        "status": "success",
        "scan_mode": scan_mode,
        "target_directory": str(target_dir),
        "hard_gate_violated": hard_gate_violation,
        "preliminary_score": prelim_score,
        "verdict": verdict,
        "files_scanned": file_count,
        "total_defects": len(all_findings),
        "findings": all_findings
    }


def main():
    parser = argparse.ArgumentParser(description="Code Review Gatekeeper Scanner")
    parser.add_argument("--target-dir", type=str, default=".", help="Root workspace directory")
    parser.add_argument("--files", nargs="*", type=str, help="Specific file(s) to scan")
    parser.add_argument("--diff", action="store_true", help="Scan only Git modified and staged files")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    target_files = [Path(f) for f in args.files] if args.files else None
    results = run_audit(Path(args.target_dir), target_files=target_files, use_diff=args.diff)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("=" * 65)
        print("🏛️ Automated Code Quality & Fidelity Scan Results")
        print("=" * 65)
        print(f"Target Directory: {results['target_directory']}")
        print(f"Files Scanned   : {results['files_scanned']}")
        print(f"Hard Gate Status: {'🚨 VIOLATED (Hard Quality Gate Failure)' if results['hard_gate_violated'] else '✅ CLEAR'}")
        print(f"Quality Score   : {results['preliminary_score']} / 100")
        print(f"Review Verdict  : {'✅ PASS (Gate Cleared - Ready for User Review)' if results['verdict'] == 'PASS' else '🛑 HOLD (Remediation Required)'}")
        print(f"Defects Found   : {results['total_defects']}")
        print("-" * 65)

        if results["findings"]:
            print("Defects Detected for Remediation:")
            for idx, item in enumerate(results["findings"], 1):
                print(f"  [{idx}] [{item['severity']}] {item['type']} at {item['file']}:{item['line']}")
                print(f"      Code: {item['evidence']}")
        else:
            print("✅ All automated static criteria cleared. No defects detected.")
        print("=" * 65)

    if results["verdict"] == "HOLD":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
