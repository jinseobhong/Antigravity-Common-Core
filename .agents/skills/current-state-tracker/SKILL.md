---
name: current-state-tracker
description: >-
  Inspects workspace, syncs STATE.md with standardized [REQUESTED] to [READY_FOR_AUDIT] tags, and delivers the current state sheet.
  Trigger at the start of any turn to ground physical facts and deliver the formatted state sheet to the builder.
---

# Current State Tracker Protocol (현재 상황표 인도 및 관리 프로토콜)

본 프로토콜은 본 작업자(Builder) 에이전트의 어텐션 분산을 원천 차단하고, 다중 턴 작업 환경에서 사용자 지시사항의 유실(Omission)을 방지하기 위해 **현재 작업 진행 상황표(`STATE.md`)를 작성·갱신하고 빌더에게 최신 상황표를 직접 인도(Handover)하는 서브프로세스 전용 지침**입니다.

---

## 1. 운영 원칙 (Core Operational Principles)

1. **빌더-트래커 분리 및 상태 은반 인도 (Silver Platter State Handover)**:
   - 본 빌더(Builder)는 복잡한 상황표 작성이나 디스크 상태 탐색에 인지 부하(Attention)를 낭비하지 않고 오직 구현에만 집중하여 고속도로를 질주합니다.
   - 본 스킬(서브프로세스/스크립트)이 대상 작업 공간(프로덕션 워크스페이스 `.` 또는 스테이징 샌드박스)의 물리 디스크를 직접 스캔하고 `STATE.md`를 갱신한 뒤, 완성된 규격 상황표를 빌더에게 직접 전달(Handover)합니다.
2. **지시사항 유실 무관용 (Zero Directive Loss)**:
   - 사용자가 요청한 모든 요구사항은 실행/계획 여부와 무관하게 인입 즉시 **`[REQUESTED]`** 딱지로 등록되어 다중 턴 간 유실을 원천 차단합니다.
3. **독립적 상태 머신 (Decoupled State Machine)**:
   - 사용자의 최종 승인 여부와 내부 개발 진척도를 엄격히 분리하여, 8단계 표준 상태 딱지를 유연하게 전이합니다.
4. **군더더기 없는 린(Lean) 상황표 구조**:
   - 턴 카운트나 물리 파일 목록 같은 부가 잡음을 배제하고, 오직 **나침반(Breadcrumbs)**, **원문 지시 백로그(User Directives)**, **작업 상태 매트릭스(Task Matrix)**의 3대 핵심 블록만 유지합니다.

---

## 2. 공식 8단계 작업 상태 딱지 (State Tags Taxonomy)

| 상태 딱지 | 명칭 | 상태 정의 및 전이 조건 |
| :---: | :--- | :--- |
| **`[REQUESTED]`** | 지시 접수 | 사용자의 요구사항이 인입되었으나, 아직 구체적인 계획 수립이나 분석이 시작되지 않은 원시 대기 상태 |
| **`[PLANNED]`** | 계획 완료 | 요구사항 분석이 완료되어 산출물 파일 경로 및 턴 목표가 구체적으로 정의된 상태 |
| **`[IN_PROGRESS]`** | 구현 진행 | 현재 활성 턴에서 작업 공간 내 파일 작성/수정이 실시간으로 진행 중인 상태 (동시 1개 권장) |
| **`[STAGED]`** | 초안 작성 | 작업 공간 내에 코드가 작성되었으나, 아직 문법 검사나 실행을 거치지 않은 상태 |
| **`[VERIFIED]`** | 로컬 검증 | 작업 공간 내에서 구문 오류가 없고 로컬 단위 테스트/스모크 체크를 통과한 상태 |
| **`[BLOCKED]`** | 의존성 대기 | 선행 작업 항목이 완료되지 않아 작업을 시작할 수 없는 대기 상태 |
| **`[REVISION]`** | 보완 필요 | 게이트키퍼 심사나 자체 점검에서 결함이 발견되어 재수정이 요구되는 상태 |
| **`[READY_FOR_AUDIT]`** | 심사 대기 | 계획된 모든 세부 작업이 `[VERIFIED]`되어 게이트키퍼 일괄 심사를 요청할 준비가 완료된 상태 |

---

## 3. 상황표 관리 실행 절차 (Execution Pipeline)

1. **작업 공간 물리적 인벤토리 스캔**:
   - `python .agents/skills/current-state-tracker/scripts/inspect_state.py` 실행 (기본: 워크스페이스 루트 `.`, 스테이징 샌드박스 시 `--target-dir ./sandbox`)
   - 작업 공간 내 물리 파일 및 최신 `STATE.md` 상황표 팩트를 확보합니다.
2. **작업 항목 상태 매핑**:
   - 기존 `STATE.md`가 존재하는 경우 이를 읽고, 방금 완료된 작업의 딱지를 전이합니다 (예: `[IN_PROGRESS]` ➔ `[STAGED]` ➔ `[VERIFIED]`).
   - 사용자가 대화 도중 새롭게 추가한 지시사항이 있다면 **`[REQUESTED]`** 상태로 신규 등록합니다.
3. **`STATE.md` 파일 갱신**:
   - 아래의 3대 핵심 블록 표준 규격으로 상황표 문서를 작업 공간 최상단에 기록합니다.
4. **사전 Diff 추출 및 변경점 검토 (Pre-Promotion Diff)**:
   - 격리 샌드박스에서 작업한 경우, 프로덕션 반영 전 변경 사항을 확인하기 위해 `python .agents/skills/current-state-tracker/scripts/generate_diff.py --sandbox-dir ./sandbox --root-dir .`를 실행합니다.

---

## 4. 표준 상황표 규격 양식 (`STATE.md`)

```markdown
# 📊 작업 상황표 (STATE.md)

### 🧭 작업 나침반 (Breadcrumbs)
- **📍 마지막 완료 작업 (Last Action)**: [작업ID] [수행 액션 및 결과] ([직전 딱지] ➔ [현재 딱지])
- **🎯 현재 활성 목표 (Active Target)**: [작업ID] [이번 턴에 집중할 단일 작업]
- **⏭️ 직후 예정 단계 (Next Step)**: [작업ID] [활성 목표 직후 수행할 조치]

---

### 📥 사용자 원문 지시 백로그 (User Directives)
- **D-01**: "[사용자 원문 지시 1]" ➔ 담당 태스크: `W-01`, `W-02`
- **D-02**: "[사용자 원문 지시 2]" ➔ 담당 태스크: `W-03`

---

### 📌 작업 상태 매트릭스 (Task Matrix)
| 작업 ID | 매핑 지시 | 작업 명세 | 상태 딱지 | 산출물 위치 (File Path) | 다음 액션 |
| :---: | :---: | :--- | :---: | :--- | :--- |
| **W-01** | D-01 | [구체적 작업 내용] | `[VERIFIED]` | `src/...` | 문법 검증 및 로컬 테스트 완료 |
| **W-02** | D-01 | [구체적 작업 내용] | `[IN_PROGRESS]` | `src/...` | 핵심 로직 구현 중 |
| **W-03** | D-02 | [구체적 작업 내용] | `[PLANNED]` | `src/...` | W-02 완료 후 착수 예정 |
| **W-04** | D-02 | [사용자 추가 지시 사항] | `[REQUESTED]` | *(미정)* | 지시 접수 완료 (계획 미착수) |
```
