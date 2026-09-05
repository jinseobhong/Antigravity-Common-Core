#!/usr/bin/env python3
"""
Directive Intent Classifier (사용자 지시사항 인텐트 분류기)
Classifies user utterances into:
  1. GENERAL_CHAT     : Greetings, casual feedback, chit-chat (No STATE.md action)
  2. TECH_DISCUSSION  : Architecture questions, feasibility inquiries, opinions (No task created)
  3. CONTROL_FLOW     : Approvals, stop/proceed commands, state machine triggers
  4. REQUIREMENT      : Actionable engineering instructions requiring EARS contract:
     - REQ:DESIGN     : Blueprints, architecture sketches, drafts
     - REQ:IMPLEMENT  : Code development, bug fixes, refactoring
     - REQ:DOC        : Technical documentation, guides, rule updates
     - REQ:AUDIT      : Red-team audits, security checks, test execution
     - REQ:GOVERNANCE : Workspace confinement, lifecycle hooks, policies
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple

# Windows console UTF-8 support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


# Pattern Definitions
GENERAL_CHAT_PATTERNS = [
    r"^(?:안녕|안녕하세요|반가워|반갑습니다|수고|수고하셨|감사|고마워|고맙습니다|좋은 하루|hello|hi|thanks|thank you)",
    r"(?:수고하셨습니다|감사합니다|고맙습니다)[\.!]?$",
]

CONTROL_FLOW_PATTERNS = [
    r"^(?:승인|동의|진행|반영|적용|확인)(?:합니다|해주세요|해줘|합시다)?[\.!]?$",
    r"^(?:박아줘|박아주세요|시작합시다|출발|멈춰|중단해줘|취소해줘|롤백해줘)[\.!]?$",
    r"^(?:yes|y|ok|okay|approve|proceed|continue|stop|cancel)[\.!]?$",
    r"(?:승인합니다|동의합니다|진행해주세요|반영해주세요|박아주세요)[\.!]?$",
]

TECH_DISCUSSION_PATTERNS = [
    r"(?:어떻게 생각|어떤 생각|어때요|어떨까|어떨까요|생각하는 지만|생각만|어떻게 보시)",
    r"(?:가능한가|가능할까|할 수 있나|할 수 있을까|못해요|안 되나요|안되나요|불가능한가|안될텐데|않나요|않을까요|아닌가요|어떻게 된)",
    r"(?:차이가 뭐|이유가 뭐|왜 그런|원인이 뭐|무슨 뜻|의미가 뭐|어떤 역할|뭐가 문제|뭐가문제)",
    r"(?:있어야 될거 같은데|있어야될거같은데|필요하지 않나|필요할 것 같은데|어떻게 생각해)",
    r"(?:what do you think|is it possible|how does|why is|what is)",
]

# Actionable Request Imperatives
ACTION_VERB_PATTERNS = [
    r"(?:짜줄래|짜줘|만들어줄래|만들어줘|해줄래|해줘|작성해줘|구현해줘|추가해줘|수정해줘|개발해줘|구축해줘|정리해줘)",
]

# Requirement Sub-category Patterns
REQ_DESIGN_PATTERNS = [
    r"(?:초안|기획|설계|아키텍처|블루프린트|스케치|구상|구조도|draft|blueprint|architecture|design|sketch)",
]

REQ_DOC_PATTERNS = [
    r"(?:문서|가이드|설명서|규격서|가이드라인|README|SKILL\.md|GEMINI\.md|doc|document|guide|manual)",
]

REQ_AUDIT_PATTERNS = [
    r"(?:검수|감사|테스트|점검|심사|레드팀|취약점|동작 확인|돌아가는 지|확인해|검사해|audit|test|verify|check|inspect)",
]

REQ_GOVERNANCE_PATTERNS = [
    r"(?:거버넌스|권한|격리|샌드박스만|잠금|차단|수칙|정책|라이프사이클|훅|hook|policy|governance|isolation|confinement)",
]

REQ_IMPLEMENT_PATTERNS = [
    r"(?:구현|개발|만들어|작성|생성|추가|수정|변경|리팩토링|패치|코딩|implement|build|create|write|add|modify|refactor|fix)",
]


def classify_text(text: str) -> Dict[str, Any]:
    """Classify user text into primary intent and sub-intent."""
    clean_text = text.strip()
    if not clean_text:
        return {
            "text": "",
            "primary_intent": "GENERAL_CHAT",
            "sub_intent": None,
            "is_actionable": False,
            "action_policy": "No action needed for empty input",
            "suggested_pipeline": "NONE"
        }

    # 1. Check General Chat
    for pat in GENERAL_CHAT_PATTERNS:
        if re.search(pat, clean_text, re.IGNORECASE):
            if not any(re.search(p, clean_text, re.IGNORECASE) for p in REQ_IMPLEMENT_PATTERNS + REQ_DESIGN_PATTERNS + ACTION_VERB_PATTERNS):
                return {
                    "text": clean_text,
                    "primary_intent": "GENERAL_CHAT",
                    "sub_intent": None,
                    "is_actionable": False,
                    "action_policy": "Respond conversationally; do not register in STATE.md.",
                    "suggested_pipeline": "CHAT_RESPONSE"
                }

    # 2. Check Control Flow (exact short confirmations/approvals)
    for pat in CONTROL_FLOW_PATTERNS:
        if re.search(pat, clean_text, re.IGNORECASE):
            if not any(re.search(p, clean_text, re.IGNORECASE) for p in TECH_DISCUSSION_PATTERNS + ACTION_VERB_PATTERNS):
                return {
                    "text": clean_text,
                    "primary_intent": "CONTROL_FLOW",
                    "sub_intent": None,
                    "is_actionable": False,
                    "action_policy": "Transition existing task states; trigger next planned stage.",
                    "suggested_pipeline": "STATE_TRANSITION"
                }

    # 3. Check Approved Directives (Discussions approved by user into requirements)
    if "-> 승인" in clean_text or "->승인" in clean_text:
        return {
            "text": clean_text,
            "primary_intent": "REQUIREMENT",
            "sub_intent": "REQ:IMPLEMENT",
            "is_actionable": True,
            "action_policy": "Approved directive: extract contract, implement in sandbox, audit.",
            "suggested_pipeline": "REQUIREMENTS_EXTRACTOR"
        }

    # 4. Check Tech Discussion (e.g. "어떻게 생각해?", "못해요?", "안될텐데?")
    has_discussion_phrase = any(re.search(p, clean_text, re.IGNORECASE) for p in TECH_DISCUSSION_PATTERNS)
    has_action_verb = any(re.search(p, clean_text, re.IGNORECASE) for p in ACTION_VERB_PATTERNS)

    if has_discussion_phrase and not has_action_verb:
        return {
            "text": clean_text,
            "primary_intent": "TECH_DISCUSSION",
            "sub_intent": None,
            "is_actionable": False,
            "action_policy": "Provide technical analysis/options; do not create implementation tasks.",
            "suggested_pipeline": "TECHNICAL_EXPLANATION"
        }

    # If it ends with question mark and doesn't contain explicit creation commands
    if clean_text.endswith("?") and not has_action_verb and not any(re.search(p, clean_text, re.IGNORECASE) for p in REQ_IMPLEMENT_PATTERNS):
        return {
            "text": clean_text,
            "primary_intent": "TECH_DISCUSSION",
            "sub_intent": None,
            "is_actionable": False,
            "action_policy": "Provide technical analysis/options; do not create implementation tasks.",
            "suggested_pipeline": "TECHNICAL_EXPLANATION"
        }

    # 4. Actionable Requirement Identification & Sub-categorization
    sub_intent = "REQ:IMPLEMENT"
    action_policy = "Register as D-xx in STATE.md, extract EARS contract, implement in sandbox, audit."

    if any(re.search(p, clean_text, re.IGNORECASE) for p in REQ_DESIGN_PATTERNS):
        sub_intent = "REQ:DESIGN"
        action_policy = "Draft blueprint/architecture design; request user alignment before coding."
    elif any(re.search(p, clean_text, re.IGNORECASE) for p in REQ_DOC_PATTERNS):
        sub_intent = "REQ:DOC"
        action_policy = "Draft/revise documentation in sandbox; verify via doc_audit_runner."
    elif any(re.search(p, clean_text, re.IGNORECASE) for p in REQ_AUDIT_PATTERNS):
        sub_intent = "REQ:AUDIT"
        action_policy = "Execute static scanners and invoke adversarial gatekeeper subagent."
    elif any(re.search(p, clean_text, re.IGNORECASE) for p in REQ_GOVERNANCE_PATTERNS):
        sub_intent = "REQ:GOVERNANCE"
        action_policy = "Update GEMINI.md/hooks.json rules and verify lifecycle constraints."

    return {
        "text": clean_text,
        "primary_intent": "REQUIREMENT",
        "sub_intent": sub_intent,
        "is_actionable": True,
        "action_policy": action_policy,
        "suggested_pipeline": "REQUIREMENTS_EXTRACTOR"
    }


def main():
    parser = argparse.ArgumentParser(description="Directive Intent Classifier - Input Gatekeeper for User Directives")
    parser.add_argument("--text", type=str, required=True, help="User utterance text to classify")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    result = classify_text(args.text)

    if args.json:
        sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        return 0

    print("=================================================================")
    print("🔍 [Directive Intent Classification Result (지시사항 인텐트 분석)]")
    print("=================================================================")
    print(f"• 입력 텍스트    : \"{result['text']}\"")
    print(f"• 1차 대분류     : {result['primary_intent']}")
    print(f"• 2차 소분류     : {result['sub_intent'] or 'N/A'}")
    print(f"• 태스크 생성여부: {'✅ 액션 필요 (REQUIREMENT)' if result['is_actionable'] else '❌ 비요구사항 (Non-Actionable)'}")
    print(f"• 권고 파이프라인: {result['suggested_pipeline']}")
    print(f"• 거버넌스 가이드: {result['action_policy']}")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
