#!/usr/bin/env python3
"""
Adversarial Quality Gate - Lifecycle Stop Hook
Executes at the agent termination event (Stop).
Enforces the Four-Eyes Principle (사안 원칙) mechanically:
Checks sandbox/STATE.md. If ANY task is not in [VERIFIED] state,
it blocks turn completion (decision: "continue") and forces the builder
to invoke the adversarial-gatekeeper subagent.
"""

import sys
import json
import re
from pathlib import Path

# Configure Windows console UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def check_adversarial_clearance(sandbox_dir: Path) -> dict:
    state_file = sandbox_dir / "STATE.md"
    if not state_file.exists():
        return {
            "decision": "stop",
            "reason": "STATE.md not found, skipping gate."
        }

    try:
        with open(state_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        return {
            "decision": "continue",
            "reason": f"🛑 [GATE ERROR] Cannot read STATE.md: {e}"
        }

    # Strict check: Block turn completion if any staged deliverables or revisions require audit
    unverified_tasks = []
    task_pattern = re.compile(r"\|\s*\*\*(W-\d+)\*\*\s*\|[^|]+\|[^|]+\|\s*`?(\[[A-Z_]+\])`?\s*\|")
    for line in content.splitlines():
        match = task_pattern.search(line)
        if match:
            tid = match.group(1)
            status = match.group(2)
            # Only [STAGED], [REVISION], [READY_FOR_AUDIT] require mandatory gatekeeper audit clearance.
            # [PLANNED] and [REQUESTED] represent pre-implementation states that allow user feedback.
            if status in ["[STAGED]", "[REVISION]", "[READY_FOR_AUDIT]"]:
                unverified_tasks.append(f"{tid}:{status}")

    if unverified_tasks:
        task_list_str = ", ".join(unverified_tasks)
        return {
            "decision": "continue",
            "reason": (
                f"🛑 [MECHANICAL ADVERSARIAL GATE ACTIVATED]\n"
                f"The following tasks in {state_file.as_posix()} are not cleared: [{task_list_str}].\n"
                f"Under Rule 3 (Four-Eyes Principle), the Builder cannot finish the turn without clearance.\n"
                f"You MUST call 'invoke_subagent' with TypeName='adversarial-gatekeeper' to audit the deliverables!"
            )
        }

    return {
        "decision": "stop"
    }


def main():
    # PUNCH-03: Specific exception handling without swallowed broad exception
    if "--stdin" in sys.argv:
        try:
            raw_input = sys.stdin.read()
            if raw_input.strip():
                json.loads(raw_input)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            pass

    # Multi-tier robust workspace directory resolution (production workspace first)
    script_file = Path(__file__).resolve()
    candidate_dirs = [
        Path.cwd(),  # Current workspace root (production standard)
        script_file.parents[2],  # Root directory containing .agents/hooks
        Path.cwd() / "sandbox",  # Development staging sandbox fallback
        Path.cwd().parent,
        Path.cwd().parent / "sandbox"
    ]
    target_dir = next((d for d in candidate_dirs if (d / "STATE.md").exists()), Path("."))

    result = check_adversarial_clearance(target_dir)
    # PUNCH-03: Use sys.stdout.write with ensure_ascii=True to prevent CP949 decoding crashes
    sys.stdout.write(json.dumps(result, ensure_ascii=True) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
