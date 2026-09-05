#!/usr/bin/env python3
"""
Current State Tracker - Sandbox Physical State Inspector & State Sheet Provider
Scans ./sandbox/, inspects/initializes sandbox/STATE.md, and formats the consolidated
Current State Sheet to hand over directly to the builder agent and user.
Supports programmatic state transitions for zero-markdown-hassle updates.
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime

# Windows console UTF-8 support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

IGNORED_DIRS = {".git", ".svn", "__pycache__", "node_modules", ".pytest_cache"}
VALID_TAGS = {"[REQUESTED]", "[PLANNED]", "[IN_PROGRESS]", "[STAGED]", "[VERIFIED]", "[BLOCKED]", "[REVISION]", "[READY_FOR_AUDIT]"}


def inspect_sandbox(sandbox_dir: Path) -> dict:
    sandbox_dir = sandbox_dir.resolve()

    if not sandbox_dir.exists():
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        return {
            "status": "initialized",
            "target_directory": str(sandbox_dir),
            "total_files": 0,
            "total_lines": 0,
            "files": [],
            "state_file_exists": False,
            "state_content": None
        }

    files_inventory = []
    total_lines = 0
    canonical_state_path = (sandbox_dir / "STATE.md").resolve()

    for root, dirs, files in os.walk(sandbox_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(sandbox_dir).as_posix()

            # PUNCH-03 fix: Only ignore the root STATE.md
            if file_path.resolve() == canonical_state_path:
                continue

            try:
                stat = file_path.stat()
                size_bytes = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()

                line_count = 0
                if file_path.suffix.lower() in {".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs", ".java", ".md", ".json", ".yaml", ".yml", ".txt", ".sh"}:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            line_count = sum(1 for _ in f)
                    except (OSError, UnicodeDecodeError):
                        # PUNCH-02 fix: Narrow specific exception
                        line_count = 0

                total_lines += line_count
                files_inventory.append({
                    "path": rel_path,
                    "size_bytes": size_bytes,
                    "line_count": line_count,
                    "modified_at": mtime
                })
            except OSError:
                # PUNCH-02 fix: Narrow specific exception
                continue

    state_file = sandbox_dir / "STATE.md"
    state_content = None
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8", errors="ignore") as f:
                state_content = f.read()
        except (OSError, UnicodeDecodeError):
            state_content = None

    return {
        "status": "active",
        "target_directory": str(sandbox_dir),
        "total_files": len(files_inventory),
        "total_lines": total_lines,
        "state_file_exists": state_file.exists(),
        "state_content": state_content,
        "files": files_inventory
    }


def update_state_tag(state_file: Path, task_id: str, new_tag: str, new_action: str = None) -> bool:
    if not state_file.exists():
        return False

    with open(state_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    target_clean = task_id.replace("*", "").strip()

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            new_lines.append(line)
            continue

        parts = [p.strip() for p in stripped.split("|")]
        if len(parts) < 6 or parts[1].replace("*", "").strip() != target_clean:
            new_lines.append(line)
            continue

        for tag in VALID_TAGS:
            if f"`{tag}`" in line:
                line = line.replace(f"`{tag}`", f"`{new_tag}`")
                updated = True
                break
            elif tag in line:
                line = line.replace(tag, f"`{new_tag}`")
                updated = True
                break

        if new_action and updated:
            table_parts = [p.strip() for p in line.split("|")]
            if len(table_parts) >= 7:
                table_parts[-2] = new_action
                joined = " | ".join(table_parts[1:-1])
                line = f"| {joined} |\n"

        new_lines.append(line)

    if updated:
        with open(state_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    return updated


def update_last_action(state_file: Path, last_action: str = None, active_target: str = None, next_step: str = None) -> bool:
    if not state_file.exists():
        return False

    with open(state_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # PUNCH-01 fix: Use lambda replacer to prevent re.error on backslashes in Windows paths
    if last_action:
        content = re.sub(
            r"(- \*\*📍 마지막 완료 작업 \(Last Action\)\*\*:\s*).*",
            lambda m: m.group(1) + last_action,
            content
        )
    if active_target:
        content = re.sub(
            r"(- \*\*🎯 현재 활성 목표 \(Active Target\)\*\*:\s*).*",
            lambda m: m.group(1) + active_target,
            content
        )
    if next_step:
        content = re.sub(
            r"(- \*\*⏭️ 직후 예정 단계 \(Next Step\)\*\*:\s*).*",
            lambda m: m.group(1) + next_step,
            content
        )

    with open(state_file, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def main():
    parser = argparse.ArgumentParser(description="Workspace Current State Inspector & State Sheet Provider")
    parser.add_argument("--target-dir", type=str, default=".", help="Target workspace directory to inspect (default: .)")
    parser.add_argument("--files", action="store_true", help="Display full physical file inventory list")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    
    # State update helper flags
    parser.add_argument("--update-tag", nargs=2, metavar=("TASK_ID", "NEW_TAG"), help="Update task tag in STATE.md")
    parser.add_argument("--new-action", type=str, default=None, help="Update next action column when updating tag")
    parser.add_argument("--set-action", type=str, help="Update Last Action in Breadcrumbs")
    parser.add_argument("--set-target", type=str, help="Update Active Target in Breadcrumbs")
    parser.add_argument("--set-next", type=str, help="Update Next Step in Breadcrumbs")
    
    args = parser.parse_args()
    target_path = Path(args.target_dir)
    state_file = target_path / "STATE.md"

    # Handle state mutations if requested
    if args.update_tag:
        tid, tag = args.update_tag
        if not tag.startswith("["):
            tag = f"[{tag}]"
        ok = update_state_tag(state_file, tid, tag, args.new_action)
        if ok:
            print(f"[SUCCESS] Updated {tid} to {tag} in {state_file}")
        else:
            print(f"[WARN] Could not find {tid} to update in {state_file}")

    if args.set_action or args.set_target or args.set_next:
        update_last_action(state_file, args.set_action, args.set_target, args.set_next)
        print(f"[SUCCESS] Updated breadcrumbs in {state_file}")

    results = inspect_sandbox(target_path)

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    print("=" * 65)
    print("📊 [현재 상황표 전달 (Current State Sheet Handover)]")
    print("=" * 65)
    print(f"• 작업 공간  : {results['target_directory']}")
    print(f"• 작업 공간 파일: {results['total_files']}개 파일 ({results['total_lines']} 라인)")
    print(f"• STATE.md   : {'✅ 최신 상태표 존재' if results['state_file_exists'] else '⚠️ 상태표 미생성 (초기화 필요)'}")
    print("-" * 65)

    if args.files and results["files"]:
        print("물리적 파일 인벤토리:")
        for f in results["files"]:
            print(f"  • {f['path']} ({f['line_count']} lines, {f['size_bytes']} bytes)")
        print("-" * 65)

    if results["state_content"]:
        breadcrumbs = []
        directives = []
        task_matrix = []
        current_section = None

        for line in results["state_content"].splitlines():
            s = line.strip()
            if "작업 나침반" in s or "Breadcrumbs" in s:
                current_section = "breadcrumbs"
                continue
            elif "사용자 원문 지시 백로그" in s or "User Directives" in s:
                current_section = "directives"
                continue
            elif "작업 상태 매트릭스" in s or "Task Matrix" in s:
                current_section = "matrix"
                continue
            elif s.startswith("## ") or s.startswith("# "):
                current_section = None

            if current_section == "breadcrumbs" and s.startswith("- "):
                breadcrumbs.append(s)
            elif current_section == "directives" and s.startswith("- "):
                directives.append(s)
            elif current_section == "matrix" and s.startswith("|") and not s.startswith("| :---"):
                task_matrix.append(s)

        if breadcrumbs:
            print("🧭 작업 나침반 (Breadcrumbs):")
            for bc in breadcrumbs:
                print(f"  {bc}")
            print("-" * 65)

        if directives:
            print("📥 사용자 원문 지시 백로그 (Directives):")
            for d in directives:
                print(f"  {d}")
            print("-" * 65)

        if task_matrix:
            print("📌 작업 상태 매트릭스 (Task Matrix):")
            for tm in task_matrix:
                print(f"  {tm}")

    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
