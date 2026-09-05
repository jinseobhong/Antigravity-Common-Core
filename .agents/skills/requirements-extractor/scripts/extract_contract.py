#!/usr/bin/env python3
"""
Requirements Extractor - Enterprise Contract Parser & Generator
Parses user directives and generates rigorous EARS-compliant Acceptance Contracts.
Integrates directly with STATE.md to bind acceptance criteria to development tasks.
"""

import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Windows console UTF-8 support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def classify_text(text: str) -> Dict[str, Any]:
    """Lightweight specification helper for sub-intent categorization."""
    clean = text.strip()
    if any(k in clean for k in ["문서", "가이드", "doc", "README", "규격서"]):
        sub = "REQ:DOC"
    elif any(k in clean for k in ["초안", "설계", "구조", "draft", "design"]):
        sub = "REQ:DESIGN"
    elif any(k in clean for k in ["감사", "검수", "테스트", "audit", "verify"]):
        sub = "REQ:AUDIT"
    elif any(k in clean for k in ["거버넌스", "권한", "격리", "policy", "hook", "규약"]):
        sub = "REQ:GOVERNANCE"
    else:
        sub = "REQ:IMPLEMENT"
    return {
        "text": clean,
        "primary_intent": "REQUIREMENT",
        "sub_intent": sub,
        "is_actionable": True
    }


classify_intent = classify_text


def resolve_directive_from_state(directive_id: str, target_dir: Path) -> tuple[str | None, str | None]:
    """Search target_dir for STATE.md and extract directive text and mapped task ID."""
    candidates = [
        target_dir / "STATE.md",
        target_dir / "sandbox" / "STATE.md",
        target_dir.parent / "STATE.md",
        Path("STATE.md"),
        Path("sandbox/STATE.md"),
    ]

    for candidate in candidates:
        if candidate.exists():
            try:
                content = candidate.read_text(encoding="utf-8", errors="ignore")
                pattern = (
                    r"-\s*\*\*"
                    + re.escape(directive_id)
                    + r"\*\*:\s*\"([^\"]+)\"(?:[^\n]*?담당 태스크:\s*`([^`]+)`)?"
                )
                match = re.search(pattern, content)
                if match:
                    text = match.group(1).strip()
                    task = match.group(2).strip() if match.group(2) else None
                    return text, task
            except OSError:
                continue
    return None, None


def decompose_directive(directive_id: str, directive_text: str, task_id: str = "W-TBD") -> Dict[str, Any]:
    """Decompose raw directive into 4-pillar enterprise requirements contract with intent routing."""
    intent_info = classify_text(directive_text)
    primary_intent = intent_info.get("primary_intent", "REQUIREMENT")
    sub_intent = intent_info.get("sub_intent") or "REQ:IMPLEMENT"

    # Clean display slicing with ellipsis if text exceeds 40 chars
    display_text = directive_text[:40] + "..." if len(directive_text) > 40 else directive_text

    # Pillar 1: Sub-intent Specialized Functional EARS
    if sub_intent == "REQ:DESIGN":
        p1_syntax = f"WHEN the user requests architecture or design for '{display_text}', the system SHALL draft a rigorous technical blueprint and structural plan without premature code commits."
        p1_pass = "Design blueprint drafted with clear architectural contracts and user alignment"
        p1_hold = "Vague design, missing trade-off analysis, or untracked file generation"
    elif sub_intent == "REQ:DOC":
        p1_syntax = f"WHEN the user requests technical documentation for '{display_text}', the system SHALL write or update target markdown files following heading hierarchy with zero placeholders."
        p1_pass = "All documentation requirements verified with exit code 0 by doc_audit_runner"
        p1_hold = "Unclosed fences, broken heading hierarchy, or missing sections"
    elif sub_intent == "REQ:AUDIT":
        p1_syntax = f"WHEN the user requests adversarial audit or validation for '{display_text}', the system SHALL execute static scanners and red-team checks, reporting pass/fail with punch list."
        p1_pass = "Complete execution of audit suite with defect punch list and score >= 90"
        p1_hold = "Unrun tests, skipped boundary checks, or unhandled exceptions"
    elif sub_intent == "REQ:GOVERNANCE":
        p1_syntax = f"WHEN the user requests governance policy enforcement for '{display_text}', the system SHALL enforce sandbox confinement, lifecycle hooks, and Four-Eyes gatekeeping."
        p1_pass = "Zero root mutations, active Stop hook enforcement, and verified gate status"
        p1_hold = "Bypassed quality gate, unauthorized root modifications, or absent hooks"
    else:  # REQ:IMPLEMENT
        p1_syntax = f"WHEN the user invokes the requested capability for '{display_text}', the system SHALL execute the target functionality completely without stubbing, verified with accompanying automated tests."
        p1_pass = "All functional specifications implemented and verified by accompanying unit tests (exit code 0)"
        p1_hold = "Omission of core capabilities, missing tests, or presence of unimplemented/pass stubs"

    contracts = []
    contracts.append({
        "req_id": "REQ-01",
        "pillar": f"Functional ({sub_intent})",
        "syntax": p1_syntax,
        "rfc2119": "MUST",
        "condition": "Valid inputs and execution environment",
        "pass_criteria": p1_pass,
        "hold_criteria": p1_hold
    })

    # Pillar 2: Interface & Schema Contract
    contracts.append({
        "req_id": "REQ-02",
        "pillar": "Interface Contract",
        "syntax": "The system SHALL enforce strict argument parsing, type validation, and standardized output schemas.",
        "rfc2119": "MUST",
        "condition": "CLI arguments, JSON configurations, or API payloads",
        "pass_criteria": "Proper schema validation with accurate help messages and structured output",
        "hold_criteria": "Malformed schemas, missing arguments crashing without helpful usage text"
    })

    # Pillar 3: NFR & Reliability
    contracts.append({
        "req_id": "REQ-03",
        "pillar": "Enterprise NFR",
        "syntax": "IF unexpected system errors, missing parent directories, or non-UTF8 encodings occur, THEN the system SHALL handle them gracefully without crashing.",
        "rfc2119": "MUST",
        "condition": "Boundary values, non-existent directories, Windows CP949 encoding",
        "pass_criteria": "Idempotent execution, graceful exception handling, and encoding robustness",
        "hold_criteria": "Unhandled exceptions (e.g. FileNotFoundError, UnicodeDecodeError), double newlines"
    })

    # Pillar 4: Adversarial Rejection Invariant
    contracts.append({
        "req_id": "REQ-04",
        "pillar": "Adversarial Invariant",
        "syntax": "The system SHALL preserve target production baselines and verify zero unintended mutations.",
        "rfc2119": "MUST NOT",
        "condition": "Blast radius checks and quality gate audit",
        "pass_criteria": "Strict blast radius control and 100% audit score from adversarial gatekeeper",
        "hold_criteria": "Uncontrolled file mutations, hard quality gate violations, score < 90"
    })

    return {
        "directive_id": directive_id,
        "directive_text": directive_text,
        "task_id": task_id,
        "primary_intent": primary_intent,
        "sub_intent": sub_intent,
        "is_actionable": intent_info.get("is_actionable", True),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "standards": ["ISO/IEC/IEEE 29148", "RFC 2119", "EARS"],
        "contracts": contracts
    }


# Backwards compatibility alias
extract_acceptance_contract = decompose_directive


def format_contract_markdown(contract_data: Dict[str, Any]) -> str:
    """Format contract data into standard Markdown table."""
    lines = []
    lines.append(f"# 📜 인수 계약서 (Acceptance Contract: {contract_data['directive_id']})")
    lines.append("")
    lines.append(f"- **원문 지시**: \"{contract_data['directive_text']}\"")
    lines.append(f"- **인텐트 분류**: `{contract_data.get('primary_intent', 'REQUIREMENT')}` ({contract_data.get('sub_intent', 'REQ:IMPLEMENT')})")
    lines.append(f"- **체결 일시**: {contract_data['timestamp']}")
    lines.append(f"- **담당 태스크**: `{contract_data['task_id']}`")
    lines.append(f"- **적용 표준**: {', '.join(contract_data['standards'])}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📋 4대 기둥 인수 계약 매트릭스 (Acceptance Contract Matrix)")
    lines.append("")
    lines.append("| 계약 ID | 분류 | EARS 구문 명세 | RFC 2119 | 수락 판정 기준 (PASS) | 적대적 거부 조건 (HOLD) |")
    lines.append("| :---: | :--- | :--- | :---: | :--- | :--- |")

    for c in contract_data["contracts"]:
        lines.append(f"| **{c['req_id']}** | {c['pillar']} | {c['syntax']} | `{c['rfc2119']}` | {c['pass_criteria']} | {c['hold_criteria']} |")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Enterprise Requirements & Acceptance Contract Extractor")
    parser.add_argument("--directive-id", "--directive", dest="directive_id", type=str, default=None, help="Directive ID (e.g. D-09)")
    parser.add_argument("--text", type=str, default=None, help="Raw user directive text (optional if directive-id exists in STATE.md)")
    parser.add_argument("--task-id", type=str, default="W-NEW", help="Mapped task ID (e.g. W-21)")
    parser.add_argument("--target-dir", type=str, default=".", help="Target workspace directory (default: .)")
    parser.add_argument("--output", type=str, default=None, help="Output contract markdown filepath")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--force", action="store_true", help="Force contract generation even if non-actionable")
    args = parser.parse_args()

    target_path = Path(args.target_dir).resolve()
    directive_id = args.directive_id or "D-NEW"
    directive_text = args.text
    task_id = args.task_id

    if not directive_text:
        # Automatic resolution from STATE.md in target-dir
        resolved_text, resolved_task = resolve_directive_from_state(directive_id, target_path)
        if resolved_text:
            directive_text = resolved_text
            if task_id == "W-NEW" and resolved_task:
                task_id = resolved_task
        else:
            sys.stderr.write(f"[ERROR] Directive text not provided and '{directive_id}' not found in STATE.md under {target_path}.\n")
            sys.stderr.write("Please provide --text \"<directive text>\" or check your --directive-id and --target-dir.\n")
            return 1

    data = decompose_directive(directive_id, directive_text, task_id)

    if not data["is_actionable"] and not args.force:
        sys.stderr.write(f"[INFO] Directive '{directive_id}' classified as non-actionable intent: {data['primary_intent']}.\n")
        sys.stderr.write("Formal acceptance contract not required. Use --force to generate anyway.\n")
        if args.json:
            sys.stdout.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        return 0

    if args.json:
        sys.stdout.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        return 0

    md_output = format_contract_markdown(data)
    sys.stdout.write(md_output + "\n")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_output, encoding="utf-8")
        sys.stdout.write(f"\n[SUCCESS] Contract saved to: {out_path}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
