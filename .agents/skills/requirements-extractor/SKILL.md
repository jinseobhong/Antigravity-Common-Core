---
name: requirements-extractor
description: >-
  Extracts and formalizes enterprise-grade requirements and acceptance contracts from user directives using EARS syntax, strict interface contracts, and adversarial rejection criteria.
  Trigger upon receiving new user requests or during blueprint planning to ground acceptance criteria before implementation.
---

# Requirements Extractor Protocol (엔터프라이즈 요구사항 및 인수 계약 검출 프로토콜)

본 프로토콜은 작업자(Builder) 에이전트가 모호하거나 러프한 사용자 프롬프트를 자의적으로 해석하여 발생하는 재작업(Rework)과 적대적 감시자(Gatekeeper)의 거부(HOLD)를 선제 방어하기 위해, **사용자 요구사항을 국제 표준(ISO/IEC/IEEE 29148, RFC 2119, EARS) 기반의 엄격한 인수 계약(Acceptance Contract)으로 정밀 분해·추출하는 입구 게이트 전용 행동 지침**입니다.

---

## 1. 운영 원칙 (Core Operational Principles)

1. **사전 계약 우선주의 (Contract-First Governance)**:
   - 코드를 한 줄이라도 작성하기 전에 반드시 명확한 수락 기준(Acceptance Criteria)과 불변식(Invariants)을 사전 정의합니다.
   - 제작자(Builder)는 "어떻게 구현할까?"를 고민하기 전에 "감시자가 나를 탈락시킬 거부 조건(HOLD Criteria)이 무엇인가?"를 역산하여 방어적으로 계약을 체결합니다.
2. **사안 원칙(Four-Eyes)의 3권 분립 완성**:
   - **출제자 (Requirements Extractor)**: 인수 기준 및 거부 조건을 정밀 도출하여 시험 문제를 출제.
   - **수험생 (Builder)**: 확정된 계약 체크리스트를 바탕으로 어텐션 분산 없이 구현에 전념.
   - **채점관 (Adversarial Gatekeeper)**: 도출된 계약 + 가혹한 엣지 케이스로 최종 심사 및 거부권 행사.
3. **자연어 모호성 제로 (Zero Natural Language Ambiguity)**:
   - "적절하게 처리한다", "빠르게 동작한다"와 같은 주관적 형용사를 전면 배제하고, EARS 조건문과 구체적인 임계값(Threshold), 타입 스키마로 계량화합니다.

---

## 2. 4대 엔터프라이즈 요구사항 검출 기둥 (The 4 Pillars)

```text
[Pillar 1: EARS 기능 명세 (FR)]
  • Ubiquitous (항상 SHALL)
  • Event-driven (WHEN ~ SHALL)
  • State-driven (WHILE ~ SHALL)
  • Error-handling (IF ~ THEN SHALL)

[Pillar 2: 데이터 & 인터페이스 엄격 계약]
  • Input/Output Types & Pydantic/JSON Schemas
  • Nullability, Min/Max Ranges, Enums
  • Pre-conditions, Post-conditions, Invariants

[Pillar 3: 엔터프라이즈 비기능 요건 (NFR)]
  • 멱등성 (Idempotency) & 무상태성 (Statelessness)
  • 실행 타임아웃 & 기한 (Timeouts/Deadlines)
  • 예외 격리 (Fault Isolation & Graceful Degradation)
  • 플랫폼 안전성 (UTF-8/CP949 인코딩, Zero Secret Leak)

[Pillar 4: 적대적 거부 조건 (Rejection Criteria)]
  • Fuzzing / Boundary (0, None, Empty, Negative)
  • 디렉토리 부재 / 리소스 고갈 방어
  • 스텁 탐지 (TODO, pass, stub) 즉시 탈락
```

---

## 3. 요구사항 추출 실행 절차 (Execution Pipeline)

1. **사전 규격 합의 제약 게이트 (Pre-Agreement Constraint Gate)**:
   - 모호한 인텐트 추측 대신 명시적 엔지니어링 제약을 적용합니다 (Fast-Track 원천 차단).
   - 사용자 발화 인입 시 독단적인 파일 생성/코드 수정 착수를 엄격히 금지하고, 먼저 `extract_contract.py`를 실행하여 4대 기둥 인수 규격을 도출합니다.
   - 사용자에게 규격을 제시하고 명시적 사전 동의(`"네 진행합시다"` 등)를 획득한 후에만 구현 태스크에 착수합니다.
   *(필요 시 하위 호환 도구인 `classify_intent.py`를 통해 지시사항 소분류를 확인할 수 있습니다.)*

2. **4대 기둥 인수 계약 체결**:
   - `extract_contract.py`를 실행하여 소분류(`REQ:DESIGN`, `REQ:DOC`, `REQ:AUDIT`, `REQ:GOVERNANCE`, `REQ:IMPLEMENT`)에 최적화된 EARS 인수 계약을 도출합니다:
   ```powershell
   # 모드 A: STATE.md 자동 연동 모드 (권장: 상황표에서 지시문 및 매핑 태스크 자동 추출)
   python .agents/skills/requirements-extractor/scripts/extract_contract.py --directive-id "D-10" --target-dir .

   # 모드 B: 원문 직접 주입 모드 (신규 지시 인입 즉시 계약 도출)
   python .agents/skills/requirements-extractor/scripts/extract_contract.py --directive-id "D-NEW" --text "사용자 지시사항 원문" --task-id "W-25"
   ```
3. **`STATE.md` 및 인수 계약 바인딩**:
   - 도출된 요구사항(`REQ-01`, `REQ-02`...)을 세부 태스크(`W-xx`)에 매핑하고 `[PLANNED]` 상태로 등록합니다.
4. **빌더 은반 인도**:
   - 빌더는 생성된 계약 표를 체크리스트 삼아 순차적으로 구현하고 산출물을 `[STAGED]`로 전이합니다.
5. **적대적 감시자 감사 연계**:
   - 감시자는 계약서의 '수락 판정 기준'과 '적대적 거부 조건'을 입력으로 삼아 적대적 난타를 수행합니다.

---

## 4. 표준 인수 계약서 서식 (`CONTRACT.md`)

```markdown
# 📜 인수 계약서 (Acceptance Contract: [지시 ID])

- **원문 지시**: "[사용자 원문 지시 내용]"
- **체결 일시**: [YYYY-MM-DD HH:MM]
- **적용 모드**: [ 프로덕션 직접 모드 (.) | 격리 샌드박스 모드 (./sandbox/) ]

### 📋 인수 계약 매트릭스 (Contract Matrix)
| 계약 ID | EARS 구문 명세 | RFC 2119 | 입력/경계값 조건 | 수락 판정 기준 (PASS) | 적대적 거부 조건 (HOLD) |
| :---: | :--- | :---: | :--- | :--- | :--- |
| **REQ-01** | [WHEN ~ SHALL] | `MUST` | [정상/비정상 입력] | [검증 가능한 기대 결과] | [적발 시 즉시 탈락 기준] |
| **REQ-02** | [IF ~ THEN SHALL] | `MUST` | [에러 시나리오] | [격리/폴백 동작] | [크래시/Unhandled Exception] |
```
