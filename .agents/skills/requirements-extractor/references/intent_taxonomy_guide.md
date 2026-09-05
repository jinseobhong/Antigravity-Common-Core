# Directive Intent Classification & Routing Guide

본 문서는 사용자 발화 인입 시 어텐션 분산과 상태표 오염을 방지하기 위한 공식 인텐트 분류 및 라우팅 규격서입니다.

---

## 1. 4대 대분류 체계 (Primary Intents)

사용자 발화는 시스템 인입 시 다음의 4대 기본 인텐트 카테고리로 엄격히 분류됩니다.

### 1. `[GENERAL_CHAT]` (일반 대화)
- **정의**: 구현과 무관한 인사, 감사, 단순 감정 표현.
- **처리**: 친절한 답변만 생성하며 `STATE.md`에 일절 등록하지 않음.

### 2. `[TECH_DISCUSSION]` (기술 질의 및 의견 교환)
- **정의**: 기술적 타당성 질문, 대안 문의, "어떻게 생각하는가?".
- **처리**: 기술적 분석과 가이드를 제시하며, 파일 작성이나 구현 태스크를 생성하지 않음.

### 3. `[CONTROL_FLOW]` (제어 및 승인)
- **정의**: 작업 승인, 중단, 롤백, 다음 단계 전환 지시.
- **처리**: 상태 머신 딱지를 전이하며 신규 지시사항(`D-xx`)으로 등록하지 않음.

### 4. `[REQUIREMENT]` (실제 엔지니어링 요구사항)
- **정의**: 코드, 문서, 설계, 규칙, 테스트에 실질적 변경을 유발하는 지시.
- **처리**: `STATE.md`에 공식 `D-xx`로 등록하고 `requirements-extractor` 계약을 체결함.

---

## 2. 5대 요구사항 세부 유형 (Requirement Sub-Intents)

| 하위 유형 | 대상 산출물 | 주요 예시 | 검증 도구 |
| :--- | :--- | :--- | :--- |
| **`REQ:DESIGN`** | 아키텍처 초안, 설계 문서 | "초안 한 번 짜줄래?" | 사용자 합의 및 사전 검토 |
| **`REQ:IMPLEMENT`** | 소스코드, CLI 유틸리티 | "분류 엔진 구현해줘" | `audit_runner.py`, 유닛테스트 |
| **`REQ:DOC`** | README, SKILL.md, API 문서 | "가이드 문서 정리해줘" | `doc_audit_runner.py` |
| **`REQ:AUDIT`** | 레드팀 감사, 정적 분석 | "실제로 돌아가는지 확인해" | `adversarial-gatekeeper` |
| **`REQ:GOVERNANCE`** | GEMINI.md, hooks.json | "샌드박스 격리 강제해라" | `enforce_adversarial_gate.py` |
