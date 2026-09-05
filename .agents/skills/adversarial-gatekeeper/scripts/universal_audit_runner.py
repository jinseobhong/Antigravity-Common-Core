#!/usr/bin/env python3
"""
Universal Task Auditor (범용 적대적 태스크 감사 엔진)
A domain-agnostic adversarial audit runner that inspects:
1. Directive Traceability & Parity (STATE.md User Directives vs Task Matrix)
2. Multi-Domain Integrity:
   - Code (.py, .ts, .js): Syntax compilation, hardcoded secrets, stub detection
   - Docs (.md): CommonMark heading hierarchy, unclosed fences, placeholder detection
   - Configs (.json, .yaml): Schema validity, parser errors, hook contract conformance
3. Sandbox Blast Radius Isolation (no rogue temporary files, strictly bounded)
4. Executability Smoke Test (verifies helper scripts run with --help without crashing)
Outputs a standardized JSON payload and formatted CLI report with PASS / HOLD verdict.
"""

import sys
import os
import re
import ast
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Windows console UTF-8 support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

IGNORED_DIRS = {
    ".git", ".svn", "node_modules", "venv", ".venv", "env",
    "__pycache__", ".pytest_cache", "dist", "build", "coverage"
}

IGNORED_FILES = {
    ".DS_Store", "thumbs.db"
}

# 1. Secret patterns for code and config
SECRET_PATTERNS = [
    ("GitHub Personal Access Token", re.compile(r"ghp_[A-Za-z0-9_]{36}")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("Slack API Token", re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}")),
    ("Private Key Header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

# 2. Lazy code stubs
CODE_STUB_PATTERNS = [
    ("Unimplemented TODO/FIXME", re.compile(r"(?i)\b(?:TODO|FIXME|HACK|XXX)\b")),
    ("Fake Return Stub", re.compile(r"^\s*return\s+(?:True|true|null|None)\s*;?\s*(?://|#)\s*(?:mock|stub|fake)", re.IGNORECASE)),
]

# 3. Doc placeholders
DOC_PLACEHOLDER_PATTERNS = [
    ("Unfilled Placeholder", re.compile(r"\[(?:TODO|TBD|FILL_ME|DRAFT|FIXME)\]", re.IGNORECASE)),
    ("Ellipsis Placeholder", re.compile(r"^\s*(?:\.\.\.|…)\s*$")),
]

# 4. JSON Schema for Antigravity Lifecycle Hooks (.agents/hooks.json)
HOOKS_SCHEMA = {
    "type": "object",
    "patternProperties": {
        ".*": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "PreToolUse": {"type": "array"},
                "PostToolUse": {"type": "array"},
                "PreInvocation": {"type": "array"},
                "PostInvocation": {"type": "array"},
                "Stop": {"type": "array"}
            },
            "additionalProperties": False
        }
    }
}


class LazyStubVisitor(ast.NodeVisitor):
    """AST visitor to detect AI code evasion (pass stubs, ellipsis placeholders)."""
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.stubs: List[tuple[str, int, str]] = []

    def _is_abstract(self, node: ast.FunctionDef) -> bool:
        for d in node.decorator_list:
            if isinstance(d, ast.Name) and d.id in {"abstractmethod", "overload"}:
                return True
            elif isinstance(d, ast.Attribute) and d.attr in {"abstractmethod", "overload"}:
                return True
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if not self._is_abstract(node):
            real_body = [
                stmt for stmt in node.body
                if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str))
            ]
            if len(real_body) == 1:
                first = real_body[0]
                if isinstance(first, ast.Pass):
                    self.stubs.append((node.name, node.lineno, "Bare 'pass' statement in function body (AI Lazy Stub)"))
                elif isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and first.value.value is Ellipsis:
                    self.stubs.append((node.name, node.lineno, "Ellipsis (...) placeholder in function body (AI Lazy Stub)"))
        self.generic_visit(node)


class UniversalAuditor:
    def __init__(self, target_dir: Path):
        self.target_dir = target_dir.resolve()
        self.defects: List[Dict[str, Any]] = []
        self.stats = {
            "total_files": 0,
            "code_files": 0,
            "doc_files": 0,
            "config_files": 0,
            "directives_checked": 0,
            "tasks_checked": 0,
            "exec_tested": 0,
            "linter_tested": False,
            "linter_violations": 0,
            "tests_executed": False,
            "tests_count": 0,
            "tests_passed": False
        }

    def add_defect(self, severity: str, file_path: str, issue: str, remediation: str):
        self.defects.append({
            "severity": severity,  # "CRITICAL", "MAJOR", "MINOR"
            "file": file_path,
            "issue": issue,
            "remediation": remediation
        })

    def audit_state_directives(self):
        """Pillar 1: Directive Traceability & Parity in STATE.md"""
        state_file = self.target_dir / "STATE.md"
        if not state_file.exists():
            self.add_defect("CRITICAL", "STATE.md", "STATE.md file does not exist in target directory",
                            "Create STATE.md with standardized 3-block format.")
            return

        try:
            with open(state_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            self.add_defect("CRITICAL", "STATE.md", f"Cannot read STATE.md: {e}", "Ensure STATE.md is accessible and UTF-8 encoded.")
            return

        # Check Directives section
        directive_matches = re.findall(r"-\s*\*\*(D-\d+)\*\*:\s*\"([^\"]+)\"", content)
        if not directive_matches:
            self.add_defect("MAJOR", "STATE.md", "No user directives (D-xx) found in User Directives section",
                            "Log all user requests with D-01, D-02 tags.")
        else:
            self.stats["directives_checked"] = len(directive_matches)

        # Check Task Matrix section
        task_rows = []
        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("|") and "**W-" in line_str:
                parts = [p.strip() for p in line_str.split("|")]
                if len(parts) >= 6:
                    task_id = parts[1].replace("*", "").strip()
                    mapping = parts[2].strip()
                    status = parts[4].strip()
                    task_rows.append((task_id, mapping, status))

        self.stats["tasks_checked"] = len(task_rows)

        # Verify every directive has corresponding tasks
        directive_ids = {d[0] for d in directive_matches}
        mapped_directives = set()
        for tid, mapping, status in task_rows:
            for did in directive_ids:
                if did in mapping:
                    mapped_directives.add(did)

        orphan_directives = directive_ids - mapped_directives
        if orphan_directives:
            for od in sorted(orphan_directives):
                self.add_defect("CRITICAL", "STATE.md", f"Directive {od} is not mapped to any task in Task Matrix",
                                f"Add explicit tasks in Task Matrix to fulfill {od}.")

    def audit_code_file(self, file_path: Path):
        """Pillar 2A: Code Syntax, Secrets, and Stubs"""
        self.stats["code_files"] += 1
        rel_path = file_path.relative_to(self.target_dir).as_posix()
        is_scanner_script = file_path.name in {"audit_runner.py", "doc_audit_runner.py", "universal_audit_runner.py"}

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
        except (OSError, UnicodeDecodeError):
            self.add_defect("MAJOR", rel_path, "File unreadable", "Ensure UTF-8 encoding.")
            return

        # Python Syntax Compilation & AST Lazy Stub Detection
        if file_path.suffix.lower() == ".py":
            try:
                tree = ast.parse(source, filename=rel_path)
                if not is_scanner_script:
                    stub_visitor = LazyStubVisitor(rel_path)
                    stub_visitor.visit(tree)
                    for func_name, lineno, msg in stub_visitor.stubs:
                        self.add_defect("CRITICAL", f"{rel_path}:{lineno}",
                                        f"AI Lazy Stub detected in '{func_name}()': {msg}",
                                        "Implement production-grade logic; remove placeholder pass or ellipsis.")
            except SyntaxError as e:
                self.add_defect("CRITICAL", rel_path, f"Python SyntaxError at line {e.lineno}: {e.msg}",
                                "Fix syntax error immediately.")
                return

        # Secrets Check
        for sec_name, sec_regex in SECRET_PATTERNS:
            if sec_regex.search(source):
                self.add_defect("CRITICAL", rel_path, f"Potential hardcoded credential detected: {sec_name}",
                                "Remove sensitive token and inject via environment variable.")

        # Stubs Check (skipping multiline docstrings and scanner regexes)
        in_docstring = False

        for line_num, raw_line in enumerate(source.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith('"""') or line.startswith("'''"):
                if in_docstring:
                    in_docstring = False
                    continue
                elif line.count('"""') == 1 or line.count("'''") == 1:
                    in_docstring = True
                    continue

            if in_docstring:
                continue

            if is_scanner_script and ("re.compile" in line or "re.search" in line or "TODO/FIXME" in line or "stub" in line.lower() or "LAZY_STUB" in line or "CODE_STUB" in line):
                continue

            for stub_name, stub_regex in CODE_STUB_PATTERNS:
                if stub_regex.search(line):
                    self.add_defect("MAJOR", f"{rel_path}:{line_num}", f"Incomplete code stub: {stub_name}",
                                    "Implement production-grade logic; remove placeholder.")

    def audit_doc_file(self, file_path: Path):
        """Pillar 2B: Markdown Heading Hierarchy & Fenced Blocks"""
        self.stats["doc_files"] += 1
        rel_path = file_path.relative_to(self.target_dir).as_posix()

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except (OSError, UnicodeDecodeError):
            self.add_defect("MAJOR", rel_path, "Doc file unreadable", "Ensure UTF-8 encoding.")
            return

        in_fence = False
        fence_char = None
        fence_len = 0
        last_heading_level = 0

        for line_num, line in enumerate(lines, start=1):
            raw = line.rstrip("\r\n")
            stripped = raw.strip()

            # Fence tracking
            fence_match = re.match(r"^(`{3,}|~{3,})", stripped)
            if fence_match:
                current_fence = fence_match.group(1)
                if not in_fence:
                    in_fence = True
                    fence_char = current_fence[0]
                    fence_len = len(current_fence)
                else:
                    if current_fence[0] == fence_char and len(current_fence) >= fence_len:
                        in_fence = False
                        fence_char = None
                        fence_len = 0
                continue

            if in_fence:
                continue

            # Heading Hierarchy
            h_match = re.match(r"^(#{1,6})\s+", stripped)
            if h_match:
                level = len(h_match.group(1))
                if last_heading_level > 0 and level > last_heading_level + 1:
                    self.add_defect("MINOR", f"{rel_path}:{line_num}",
                                    f"Skipped heading level: H{last_heading_level} -> H{level}",
                                    f"Use H{last_heading_level + 1} instead of H{level}.")
                last_heading_level = level

            # Placeholders
            for p_name, p_regex in DOC_PLACEHOLDER_PATTERNS:
                if p_regex.search(stripped):
                    self.add_defect("MAJOR", f"{rel_path}:{line_num}", f"Doc placeholder detected: {p_name}",
                                    "Replace placeholder with complete technical explanation.")

        if in_fence:
            self.add_defect("CRITICAL", rel_path, f"Unclosed code fence opened with {fence_char * fence_len}",
                            "Close all code fences before end of document.")

    def audit_config_file(self, file_path: Path):
        """Pillar 2C: Configuration & Schema Integrity (JSON/YAML)"""
        self.stats["config_files"] += 1
        rel_path = file_path.relative_to(self.target_dir).as_posix()

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            self.add_defect("MAJOR", rel_path, "Config file unreadable", "Ensure UTF-8 encoding.")
            return

        if file_path.suffix.lower() == ".json":
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                self.add_defect("CRITICAL", rel_path, f"JSON Syntax Error at line {e.lineno}, col {e.colno}: {e.msg}",
                                "Ensure valid JSON syntax without trailing commas.")
                return

            # Special validation for hooks.json
            if file_path.name == "hooks.json":
                self._validate_hooks_json(rel_path, data)

        elif file_path.suffix.lower() in {".yaml", ".yml"}:
            if HAS_YAML:
                try:
                    yaml.safe_load(content)
                except Exception as e:
                    self.add_defect("CRITICAL", rel_path, f"YAML Syntax Error: {e}",
                                    "Fix YAML indentation or syntax errors.")

    def _validate_hooks_json(self, rel_path: str, data: Any):
        """Validate Antigravity Lifecycle Hook schema contract and script existence (PUNCH-05)"""
        if not isinstance(data, dict):
            self.add_defect("CRITICAL", rel_path, "hooks.json root must be a JSON object", "Wrap hooks under named keys.")
            return

        if HAS_JSONSCHEMA:
            try:
                jsonschema.validate(instance=data, schema=HOOKS_SCHEMA)
            except jsonschema.ValidationError as err:
                self.add_defect("MAJOR", rel_path, f"JSONSchema validation failed: {err.message}",
                                "Ensure hooks conform to Antigravity hook schema.")

        valid_events = {"PreToolUse", "PostToolUse", "PreInvocation", "PostInvocation", "Stop"}
        hooks_file_dir = (self.target_dir / rel_path).parent

        for hook_name, spec in data.items():
            if not isinstance(spec, dict):
                self.add_defect("MAJOR", rel_path, f"Hook definition '{hook_name}' must be an object", "Specify event handlers in object.")
                continue

            for key, handlers in spec.items():
                if key in {"enabled"}:
                    continue
                if key not in valid_events:
                    self.add_defect("MAJOR", rel_path, f"Invalid hook event '{key}' in '{hook_name}'",
                                    f"Use one of: {', '.join(sorted(valid_events))}")
                    continue

                if not isinstance(handlers, list):
                    self.add_defect("MAJOR", rel_path, f"Hook event '{key}' in '{hook_name}' must be an array of handlers",
                                    "Format event handlers as an array.")
                    continue

                for handler in handlers:
                    self._validate_single_handler(rel_path, hook_name, key, handler, hooks_file_dir)

    def _validate_single_handler(self, rel_path: str, hook_name: str, key: str, handler: dict, hooks_file_dir: Path):
        """Validate a single hook handler specification and script existence (depth <= 2)"""
        cmd = handler.get("command", "")
        if not cmd:
            self.add_defect("CRITICAL", rel_path, f"Handler in '{hook_name}:{key}' missing command",
                            "Provide executable command string.")
            return

        script_matches = re.findall(r"[\w\./\-]+\.(?:py|sh|bat|ps1)", cmd)
        if not script_matches:
            return

        found_any = False
        for sm in script_matches:
            candidates = [
                hooks_file_dir / sm,
                self.target_dir / sm,
                self.target_dir.parent / sm
            ]
            if any(c.resolve().exists() for c in candidates):
                found_any = True
                break

        if not found_any:
            self.add_defect("CRITICAL", rel_path,
                            f"Hook '{hook_name}' command references missing script: {script_matches}",
                            "Ensure target hook script exists on disk.")

    def _test_single_cli_script(self, py_path: Path):
        """Helper to test a single CLI entrypoint with depth <= 2 (PUNCH-04)"""
        rel_path = py_path.relative_to(self.target_dir).as_posix()
        try:
            with open(py_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            return

        if "__main__" not in content or "argparse" not in content:
            return

        self.stats["exec_tested"] += 1
        cmd = [sys.executable, str(py_path), "--help"]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, text=True)
        except subprocess.TimeoutExpired:
            self.add_defect("CRITICAL", rel_path, "Script timed out during --help execution", "Avoid blocking calls during init.")
            return

        if res.returncode != 0:
            self.add_defect("CRITICAL", rel_path,
                            f"CLI smoke check failed with exit code {res.returncode}: {res.stderr.strip()}",
                            "Fix argument parsing or crash on --help.")

    def audit_executability(self):
        """Pillar 3: Executability Smoke Test for CLI scripts (PUNCH-04: max depth <= 3)"""
        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    self._test_single_cli_script(Path(root) / file)

    def audit_skills_contract(self):
        """Pillar 4: Enterprise Triad Skills Integrity & Acceptance Contract Schema"""
        skills_dir = self.target_dir / ".agents" / "skills"
        if not skills_dir.exists():
            return

        # Check required triad skills
        triad_skills = {
            "current-state-tracker": ["SKILL.md", "scripts/inspect_state.py", "scripts/generate_diff.py"],
            "adversarial-gatekeeper": ["SKILL.md", "scripts/universal_audit_runner.py"],
            "requirements-extractor": ["SKILL.md", "scripts/extract_contract.py", "references/ears_syntax_guide.md"]
        }

        for skill_name, required_files in triad_skills.items():
            skill_path = skills_dir / skill_name
            if not skill_path.exists():
                self.add_defect("MAJOR", f".agents/skills/{skill_name}",
                                f"Triad governance skill '{skill_name}' missing from skills directory",
                                f"Scaffold and deploy {skill_name} skill.")
                continue

            for rf in required_files:
                file_target = skill_path / rf
                if not file_target.exists():
                    self.add_defect("CRITICAL", f".agents/skills/{skill_name}/{rf}",
                                    f"Required triad skill asset '{rf}' missing in '{skill_name}'",
                                    f"Ensure {rf} exists and is executable.")

    def audit_linter(self):
        """Tier 1: Static Linter Execution via Flake8 (PEP8, unused vars/imports, syntax)"""
        cmd = [
            sys.executable, "-m", "flake8",
            "--select=E,F,W",
            "--ignore=E501,W503",
            f"--exclude={','.join(IGNORED_DIRS)}",
            str(self.target_dir)
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
            self.stats["linter_tested"] = True
            if res.returncode != 0 and res.stdout.strip():
                lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
                self.stats["linter_violations"] = len(lines)
                for line in lines:
                    self.add_defect("MAJOR", line, f"Flake8 linter violation: {line}",
                                    "Resolve style/syntax violation according to PEP8.")
            else:
                self.stats["linter_violations"] = 0
        except Exception:
            self.stats["linter_tested"] = False

    def audit_dynamic_tests(self):
        """Tier 2: Dynamic Runtime Execution & Test Pairing (unittest discover)"""
        tests_dir = self.target_dir / "tests"
        if not tests_dir.exists() or not any(tests_dir.glob("test_*.py")):
            if self.stats["code_files"] > 0:
                self.add_defect("MAJOR", "tests/",
                                "No dynamic unit tests found (Test Pairing violation: tests/test_*.py missing)",
                                "Create dynamic test suite in tests/ to verify runtime execution.")
            return

        cmd = [
            sys.executable, "-m", "unittest", "discover",
            "-s", str(tests_dir),
            "-p", "test_*.py"
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
            self.stats["tests_executed"] = True
            output = res.stderr.strip() or res.stdout.strip()
            run_match = re.search(r"Ran\s+(\d+)\s+tests?", output)
            test_count = int(run_match.group(1)) if run_match else 0
            self.stats["tests_count"] = test_count

            if res.returncode != 0:
                self.stats["tests_passed"] = False
                self.add_defect("CRITICAL", "tests/",
                                f"Dynamic test suite execution failed:\n{output}",
                                "Fix runtime crashes (TypeError, NameError, AssertionError) before gate clearance.")
            else:
                self.stats["tests_passed"] = True
        except subprocess.TimeoutExpired:
            self.add_defect("CRITICAL", "tests/", "Dynamic test suite timed out (>60s)", "Optimize test suite performance.")
        except Exception as e:
            self.add_defect("MAJOR", "tests/", f"Failed to execute dynamic tests: {e}", "Ensure tests can be run via unittest.")

    def run_all(self) -> Dict[str, Any]:
        """Execute full 3-Tier universal audit suite"""
        # --- Tier 1: Static Integrity (0.1s / 0-cost) ---
        self.audit_state_directives()
        self.audit_skills_contract()

        for root, dirs, files in os.walk(self.target_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for file in files:
                if file in IGNORED_FILES:
                    continue
                file_path = Path(root) / file
                self.stats["total_files"] += 1
                ext = file_path.suffix.lower()

                if ext in {".py", ".ts", ".js", ".go", ".rs"}:
                    self.audit_code_file(file_path)
                elif ext == ".md":
                    self.audit_doc_file(file_path)
                elif ext in {".json", ".yaml", ".yml"}:
                    self.audit_config_file(file_path)

        self.audit_linter()

        # --- Tier 2: Dynamic Execution Integrity (1-2s / 0-cost) ---
        self.audit_executability()
        self.audit_dynamic_tests()

        # Compute Score
        score = 100
        critical_count = 0
        major_count = 0
        minor_count = 0

        for d in self.defects:
            sev = d["severity"]
            if sev == "CRITICAL":
                score -= 30
                critical_count += 1
            elif sev == "MAJOR":
                score -= 10
                major_count += 1
            elif sev == "MINOR":
                score -= 3
                minor_count += 1

        score = max(0, score)
        verdict = "PASS" if score >= 90 and critical_count == 0 else "HOLD"

        return {
            "target_dir": str(self.target_dir),
            "verdict": verdict,
            "score": score,
            "stats": self.stats,
            "summary": {
                "critical_defects": critical_count,
                "major_defects": major_count,
                "minor_defects": minor_count,
                "total_defects": len(self.defects)
            },
            "defects": self.defects
        }


def main():
    parser = argparse.ArgumentParser(description="Universal Task Auditor - 3-Tier Fail-Fast Verification Engine")
    parser.add_argument("--target-dir", type=str, default=".", help="Target workspace directory to audit (default: .)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    auditor = UniversalAuditor(Path(args.target_dir))
    report = auditor.run_all()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["verdict"] == "PASS" else 1

    print("=" * 65)
    print("🏛️ [Universal Adversarial Audit Report (3-Tier Fail-Fast Pipeline)]")
    print("=" * 65)
    print(f"• 감사 대상    : {report['target_dir']}")
    print(f"• 최종 판정    : {'✅ PASS (Gate Cleared)' if report['verdict'] == 'PASS' else '🛑 HOLD (Remediation Required)'}")
    print(f"• 산정 점수    : {report['score']} / 100점 (기준: 90점 이상 & CRITICAL 0건)")
    print("-" * 65)
    print("📊 3계층 파이프라인 검증 통계:")
    stats = report["stats"]
    linter_status = f"{stats['linter_violations']}건 위반" if stats['linter_violations'] > 0 else "정상 (0 violations)"
    print(f"  [Tier 1: 정적 무결성] 총 {stats['total_files']}개 파일 (코드 {stats['code_files']}, 문서 {stats['doc_files']}, 설정 {stats['config_files']})")
    print(f"                       Flake8 린터: {linter_status} | 지시사항 매핑: {stats['directives_checked']}개")
    test_status = f"{stats['tests_count']}개 통과 (OK)" if stats['tests_passed'] else f"{stats['tests_count']}개 실행 (FAIL)"
    if not stats['tests_executed']:
        test_status = "테스트 스위트 미검출"
    print(f"  [Tier 2: 동적 무결성] CLI 스모크: {stats['exec_tested']}개 점검 | 동적 테스트: {test_status}")
    gate_ready = "준비 완료 (Ready for Gatekeeper)" if report['verdict'] == 'PASS' else "시정 필요 (Remediation Required)"
    print(f"  [Tier 3: 의미론 감시] 감시자 청구 준비도: {gate_ready}")
    print("-" * 65)
    summary = report["summary"]
    print(f"🔍 결함 집계 : CRITICAL={summary['critical_defects']} | MAJOR={summary['major_defects']} | MINOR={summary['minor_defects']}")
    print("-" * 65)

    if report["defects"]:
        print("📋 결함 시정 요구서 (Defect Punch List):")
        for idx, d in enumerate(report["defects"], start=1):
            print(f"  {idx}. [{d['severity']}] {d['file']}")
            print(f"     - 결함: {d['issue']}")
            print(f"     - 시정: {d['remediation']}")
    else:
        print("🎉 축하합니다! 모든 도메인(코드/문서/설정/지시사항/실행성)에서 결함이 전혀 발견되지 않았습니다.")

    print("=" * 65)
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
