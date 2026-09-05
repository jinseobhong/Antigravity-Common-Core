# Engineering Execution Rules

본 프로젝트에서 어떠한 작업을 수행하든, 어텐션 분산 방지와 작업 무결성(Zero Context Wipe) 보장을 위해 다음 3대 핵심 수칙을 준수하십시오.

---

## 1. 현재 상황 강제 점검 및 사전 규격 동의 제약 (Mandatory State Grounding & Pre-Agreement Constraint)
* 어떠한 작업을 시작하든, 실제 행동(파일 생성/수정/명령어 실행 등)에 착수하기 전에 **반드시 `current-state-tracker` 스킬을 최우선 실행**하여 대상 작업 공간(기본: 프로덕션 워크스페이스 `.`) 물리 상태와 최신 상황표(`STATE.md`)를 인도받으십시오.
* **사전 규격 합의 제약 게이트 (Pre-Agreement Constraint Gate - Fast-Track 원천 차단)**:
  * 불확실한 인텐트 추측(NLP Guessing)을 배제하고, 단일한 엔지니어링 제약(Constraint)을 기계적으로 적용합니다.
  * 사용자의 요구사항 인입 시, AI는 **사용자의 명시적 사전 동의 없이 독단적으로 코드 작성, 파일 생성/수정, 산출물 반영(Fast-Track)에 착수하는 것이 엄격히 금지**됩니다.
  * 변경 요청 시 먼저 `extract_contract.py`를 통해 EARS 및 RFC 2119 기준의 4대 기둥(기능, 인터페이스, NFR, 적대적 거부 조건) 인수 규격을 도출하여 사용자에게 제시하고, 사용자의 명시적 사전 승인(`"네 진행합시다"` 등)을 확인한 후에만 구현 단계로 진입합니다.
* 인도받은 사실(Fact) 및 합의된 규격에 기반하여 다음 의무 블록을 선언한 후에만 작업에 착수할 수 있습니다:
  > **`[현재 상황 및 합의 규격]: <Task ID> - <EARS 핵심 규격 요약 및 사용자 사전 승인 상태>`**

---

## 2. 전(全) 단계 필수 상태 반영 및 격리 구현 (All-Stage State Reflection & Isolation)
* **모든 작업 전이(Phase Transition) 직후에는 반드시 `STATE.md` 상황표 동기화(체크포인트 박제)를 수행**해야 합니다:
  1. **[지시 인입 시]**: 사용자 요구사항 분석 후 지체 없이 **`[REQUESTED]`** 상태로 상황표에 등록.
  2. **[계획 수립 시]**: 작업 단위 확정 후 **`[PLANNED]`** (또는 착수 시 **`[IN_PROGRESS]`**) 전이.
  3. **[구현 완료 시]**: 코드 작성 완료 즉시 산출물을 **`[STAGED]`**로 전이하고 **`[마지막 완료 작업]`** 갱신.
  4. **[검사 완료 시]**: 단위 검증 통과 시 **`[VERIFIED]`**, 결함 시 **`[REVISION]`**으로 전이.
* **프로덕션 환경 적용 및 격리 개발 원칙 (Production Standard & Isolated Staging)**:
  * 본 스위트는 **프로덕션 환경(Production Workspace, `.`)**을 1차 표준 대상으로 설계되었습니다.
  * **프로덕션 직접 작업 모드 (Direct Workspace Mode)**: 프로덕션 프로젝트 내에서 직접 작업을 수행할 때는 모든 변경사항을 `[STAGED]`로 격리하여 적대적 감시자의 검증(`[VERIFIED]`) 통과 전까지 배포/커밋을 엄격히 통제합니다.
  * **사전 격리 샌드박스 모드 (Isolated Sandbox Staging Mode)**: 프로덕션 원본 보호가 필요한 개발 단계에서는 격리 샌드박스(`./sandbox/`)에서 개발하고, `generate_diff.py`를 통해 사용자가 사전 Diff를 검토·승인한 후 프로덕션으로 승격(Promotion)합니다.

---

## 3. 자체 검사 절대 금지 및 3계층 Fail-Fast 감사 청구 (Adversarial Quality Gate Clearance)
* **제작자(Builder)는 자신이 작성한 산출물에 대해 직접 검증하거나 자의적으로 `PASS`를 선언할 권한이 일절 없습니다 (사안 원칙, Four-Eyes Principle).**
* **3계층 Fail-Fast 무결점 파이프라인 (3-Tier Verification Pipeline)**:
  1. **Tier 1 (정적 무결성 - 0.1초 / $0)**:
     - 기성 린터(`flake8 --select=E,F,W --ignore=E501,W503`)로 PEP8, 미사용 변수/임포트 100% 차단.
     - AST `LazyStubDetector`로 `pass`, `...`, 단일 더미 리턴 등 AI 꼼수/가짜 구현 즉시 색출.
     - `jsonschema` 기반 `hooks.json` 스키마 및 마크다운 헤딩/펜스 닫힘 상태 검증.
  2. **Tier 2 (동적 런타임 무결성 - 1~2초 / $0)**:
     - **테스트 페어링 (Test Pairing) 의무화**: 모든 기능 구현은 반드시 해당 동작을 실증하는 동반 단위 테스트(`tests/test_*.py`)를 함께 작성해야 합니다.
     - `unittest discover`를 통해 실제 모듈을 실행하여 `TypeError`, `NoneType`, `IndexError`, `ImportError` 등 런타임 크래시를 LLM 호출 전 기계적으로 박멸.
  3. **Tier 3 (의미론적 의도 검증 - 태스크 완료 시 1회)**:
     - 단순 문법/크래시가 앞단에서 완벽히 차단된 상태에서, 독립 서브에이전트(`adversarial-gatekeeper`)가 EARS 사용자 의도 일치도, 경계값/논리 반전, 부작용만 정밀 심사하여 LLM 비용과 지연시간을 극소화.
* **기계적 턴 종료 차단 (Mechanical Stop Gate)**:
  * 본 프로젝트는 프롬프트 수준의 지침에만 의존하지 않고, Antigravity 라이프사이클 훅(`.agents/hooks.json` 내 `Stop` 훅)을 통해 기계적으로 강제됩니다.
  * 작업 공간 내 미검증 작업(`[STAGED]`, `[IN_PROGRESS]`, `[REVISION]`)이 존재하는 상태에서 빌더가 턴을 종료하려 하면 런타임 차단막(`enforce_adversarial_gate.py`)이 작동하여 턴 종료를 강제 거부(`decision: continue`)합니다.
* **도메인 무관 범용 3계층 감사기 (Universal 3-Tier Auditor)**:
  * 3계층 파이프라인 전체(린터 ➔ AST 스텁 ➔ 동적 테스트 ➔ CLI 스모크 ➔ 지시사항 일치도)를 통합 실행하는 `universal_audit_runner.py`를 기반으로 감사를 수행합니다.
* **공식 호출 규격 (Antigravity Native Subagent Tool Call)**:
  ```json
  {
    "Subagents": [
      {
        "TypeName": "adversarial-gatekeeper",
        "Role": "Adversarial Red Team Lead",
        "Prompt": "Perform a strict adversarial red-team audit on the target environment (default: workspace root . or ./sandbox/ if in staging). Inspect STATE.md (User Directives D-01~D-12), run 3-Tier universal scanner (universal_audit_runner.py), verify dynamic tests in tests/, probe edge cases, check hooks contract (hooks.json), and issue your definitive score and PASS or HOLD verdict.",
        "Model": "inherit"
      }
    ]
  }
  ```
  *(해당 세션에 감시자가 미등록된 경우, `define_subagent` 도구로 감시자를 먼저 등록한 후 위 호출을 실행합니다.)*
* **판정 후속 조치**:
  * 감시자가 **`🛑 HOLD`** 판정 시: 즉시 `[REVISION]`으로 전이하고 결함 시정 요구서(Punch List)를 100% 반영한 후 재청구.
  * 감시자가 **`✅ PASS`** 판정 시: `[VERIFIED]` 전이 후 사용자(User)에게 최종 검토 및 승인을 요청. 에이전트가 스스로 최종 승인(`APPROVED`)을 선언할 수 없습니다.
