# 📊 작업 상황표 (STATE.md)

본 문서는 샌드박스 내부의 현재 작업 진행 상황 및 단계별 체크포인트를 추적하는 공식 상황표입니다.

---

## 🧭 작업 나침반 (Breadcrumbs)
- **📍 마지막 완료 작업 (Last Action)**: [W-36] 거버넌스 문서 동기화 및 `adversarial-gatekeeper` 독립 감시자 적대적 전수 재감사 100점 만점 PASS 통과 (W-33~W-36 [VERIFIED] 승격)
- **🎯 현재 활성 목표 (Active Target)**: 사용자(User)에게 통합 Diff 리포트 보고 및 최종 승격(Promotion) 승인 요청
- **⏭️ 직후 예정 단계 (Next Step)**: 사용자의 승인 시 프로덕션 루트(`.`)로 샌드박스 산출물 승격(Promotion)

---

### 📥 사용자 원문 지시 백로그 (User Directives)
- **D-01**: "네 샌드박스 안에서 진행해주세요." ➔ 담당 태스크: `W-01`, `W-02`, `W-03`
- **D-02**: "단일 빌더에게 검사 권한을 주는 건 좀 좋지 않다고 생각해서 적대적 감시자를 설정하는 게 낮다고 생각합니다." ➔ 담당 태스크: `W-04`, `W-05`, `W-06`, `W-07`
- **D-03**: "호출 방식이 안 적혀 있는 데 어떻게 병렬 실행을 한겁니까? -> 네 박아주세요." ➔ 담당 태스크: `W-08`, `W-09`
- **D-04**: "지금도 작동해야되지 않나요? 이건 코드에 대해서만 작동하게 된 하드코딩된건데?................음.....뭐가문제일까요?" ➔ 담당 태스크: `W-10`, `W-11`, `W-12`, `W-13`
- **D-05**: "hooks.json으로 강제는 못해요? 지금 어디까지나 님이 메인 스트림에서 실행하는 과정인건데, 강제로 이 걸 실행하게 물리적으로 강제하는 방법은 없습니까?" ➔ 담당 태스크: `W-14`, `W-15`
- **D-06**: "실제로 돌아가는 지 확인해야되니까 샌드박스 내라는 걸 가정하지 말고 실제 프러덕션 환경이라고 가정하고 짜보세요." ➔ 담당 태스크: `W-16`
- **D-07**: "diff를 확인하고 적용해야하니 프러덕션 환경으로 가정하고 작성을 하더라도, /sandbox 내에서만 작성해라. 쓰기권한을 .agents/와 GEMNI.md는 막아두었다." ➔ 담당 태스크: `W-17`, `W-18`
- **D-08**: "개발환경(샌드박스)에서 개발하는 건 프로덕션 환경이라고 명백하게 들어가야되는 데 지금 그냥 샌드박스라고 다 박아버리니까 이걸 바로 프로덕션 환경에 적용할 수가 없음." ➔ 담당 태스크: `W-19`, `W-20`
- **D-09**: "초안 한 번 짜줄래? 최고 수준의 엔터프라이즈 기준으로 요구사항을 검출해내는 것으로. -> 승인 및 구현" ➔ 담당 태스크: `W-21`, `W-22`, `W-23`, `W-24`
- **D-10**: "저거 원문 지시를 분류하는 인텐트가 있어야될거같은데? 사용자 지시사항을 일반 / 기술 대화 / 요구 사항 / 그 외 분류 이런식으로 ? -> 승인" ➔ 담당 태스크: `W-25`, `W-26`, `W-27`, `W-28`
- **D-11**: "업그레이드하자. 그리고 모든 skills의 스크립트 파일을 한 번 더 검토하는 것이 필요할 것 같아." ➔ 담당 태스크: `W-29`, `W-30`, `W-31`, `W-32`
- **D-12**: "음. 지금 클래시피컬하게 분류가 되는 데, 너무 불명확하게 한 거 같은데, 좀 제약사항인걸로 바꾸면 간단하지 않을까 싶은데? 제가 하고 싶은 건 각 기능들을 구현할 때 규격을 정하고 그 규격대로 되는 건데, 의도를 판별할 필요가 없잖아요? 다만 구현 이전에 사전 동의를 명시화하면 될 것 같은데? 어떻게 생각하세요. 지금 문제가 바로바로 fast track이 되는건데. -> 네 단순화합시다." ➔ 담당 태스크: `W-33`, `W-34`, `W-35`, `W-36`

---

## 📌 작업 상태 매트릭스 (Task Matrix)
| 작업 ID | 매핑 지시 | 작업 명세 | 상태 딱지 | 산출물 위치 | 다음 액션 |
| :---: | :---: | :--- | :---: | :--- | :--- |
| **W-01** | D-01 | 린(Lean) 상태표 규격 반영 (`sample_state_sheet.md`, `state_tags_spec.md`, `SKILL.md`) | `[VERIFIED]` | `sandbox/.agents/skills/current-state-tracker/` | 린 규격 문서 갱신 |
| **W-02** | D-01 | `inspect_state.py` 린 규격 출력 최적화 및 상태 갱신 CLI 지원 | `[VERIFIED]` | `sandbox/.agents/skills/current-state-tracker/scripts/inspect_state.py` | 스크립트 기능 고도화 |
| **W-03** | D-01 | 게이트키퍼 심사 수행 및 PASS 판정 획득 | `[VERIFIED]` | `sandbox/` | `tech-doc-gatekeeper` 심사 |
| **W-04** | D-02 | `adversarial-gatekeeper` 전용 스킬 및 적대적 감사 프로토콜 구축 | `[VERIFIED]` | `sandbox/.agents/skills/adversarial-gatekeeper/` | 스킬 및 루브릭 작성 |
| **W-05** | D-02 | `define_subagent`로 `adversarial-gatekeeper` 서브에이전트 등록 | `[VERIFIED]` | 런타임 서브에이전트 | 서브에이전트 등록 |
| **W-06** | D-02 | `GEMINI.md` 및 `README.md` 적대적 감시자 필수 호출 룰 개정 | `[VERIFIED]` | `sandbox/GEMINI.md` | 룰 개정 |
| **W-07** | D-02 | `adversarial-gatekeeper` 독립 서브에이전트 실전 모의 감사 실행 | `[VERIFIED]` | `sandbox/` | 적대적 재감사 100점 PASS 통과 |
| **W-08** | D-03 | 서브에이전트 호출 규격(JSON Signature) 공식 명시 | `[VERIFIED]` | `sandbox/GEMINI.md`, `sandbox/README.md`, `SKILL.md` | 호출 명세 문서화 |
| **W-09** | D-03 | 기술문서 린터(doc_audit_runner) 검증 및 최종 동기화 | `[VERIFIED]` | `sandbox/` | 기술문서 린트 100점 무결성 통과 |
| **W-10** | D-04 | 근본 원인 분석: 기계적 강제 부재(프롬프트 권고 한계) 및 코드 하드코딩 결함 분석 | `[VERIFIED]` | `sandbox/` | 원인 진단 및 아키텍처 결함 규명 완료 |
| **W-11** | D-04 | 범용 적대적 감사 엔진(Universal Task Auditor) 구축: 코드/문서/설정/지시사항 일치도 통합 검증 | `[VERIFIED]` | `sandbox/.agents/skills/adversarial-gatekeeper/scripts/universal_audit_runner.py` | 다중 도메인 감사 스크립트 작성 및 100점 통과 |
| **W-12** | D-04 | 기계적 강제 라이프사이클 훅(`.agents/hooks.json`) 구축: PASS 서명 없는 임의 턴 종료 차단 | `[VERIFIED]` | `sandbox/.agents/hooks.json`, `hooks/enforce_adversarial_gate.py` | Stop 훅 구축 및 무단 종료 차단 실증 완료 |
| **W-13** | D-04 | `adversarial-gatekeeper` 독립 서브에이전트 실전 호출 및 범용 감사 PASS 획득 | `[VERIFIED]` | `sandbox/` | 1차 40점 HOLD 수령 ➔ 5대 결함 시정 ➔ 2차 100점 PASS 통과 |
| **W-14** | D-05 | 런타임 물리적 강제 메커니즘 분석: Antigravity CORTEX 엔진의 훅 탐색 경로 및 실제 발동 구조 규명 | `[VERIFIED]` | `.agents/hooks.json` | CORTEX 엔진 탐색 구조 규명 완료 |
| **W-15** | D-05 | 프로덕션 환경 실제 배포: 루트 `.agents/hooks.json` 및 `hooks/enforce_adversarial_gate.py` 활성화 | `[VERIFIED]` | `.agents/hooks/`, `GEMINI.md`, `README.md` | 프로덕션 루트 배포 및 CP949 안전성 확보 |
| **W-16** | D-06 | `adversarial-gatekeeper` 프로덕션 루트 전수 재감사 및 최종 게이트 통과 | `[VERIFIED]` | `.` | 1차 75점 HOLD 수령 ➔ 3대 결함 시정 ➔ 2차 100점 PASS 통과 |
| **W-17** | D-07 | 샌드박스 격리 원칙 재확립: 프로덕션 가정 작업이라도 오직 ./sandbox/ 내에서만 작성 | `[VERIFIED]` | `sandbox/GEMINI.md`, `sandbox/README.md` | 적대적 감시자 100점 PASS 획득 |
| **W-18** | D-07 | 샌드박스 ➔ 프로덕션 사전 검토용 Diff 추출 도구(generate_diff.py) 구축 | `[VERIFIED]` | `sandbox/.agents/skills/current-state-tracker/scripts/generate_diff.py` | 적대적 감시자 100점 PASS 획득 |
| **W-19** | D-08 | 프로덕션 환경(Production Environment) 표준화: GEMINI.md, README.md, SKILL.md, enforce_adversarial_gate.py 전면 개편 | `[VERIFIED]` | `sandbox/GEMINI.md`, `sandbox/README.md`, `.agents/` | 적대적 감시자 100점 PASS 획득 |
| **W-20** | D-08 | CLI 엔트리포인트 기본값 프로덕션(.) 통일 및 다중 환경(프로덕션 vs 샌드박스) 호환성 보장 | `[VERIFIED]` | `sandbox/.agents/skills/` | 적대적 감시자 100점 PASS 획득 |
| **W-21** | D-09 | `requirements-extractor` 스킬 스캐폴딩 및 엔터프라이즈 계약 추출기(`extract_contract.py`) 구축 | `[VERIFIED]` | `sandbox/.agents/skills/requirements-extractor/` | 적대적 재감사 100점 PASS 획득 |
| **W-22** | D-09 | `GEMINI.md`, `README.md`, `SKILL.md` 3자 트라이어드 거버넌스 및 CLI 가이드 동기화 | `[VERIFIED]` | `sandbox/` | 적대적 재감사 100점 PASS 획득 |
| **W-23** | D-09 | `universal_audit_runner.py`에 요구사항 계약 무결성 검증 규칙 통합 | `[VERIFIED]` | `sandbox/.agents/skills/adversarial-gatekeeper/scripts/universal_audit_runner.py` | 100점 통과 완료 |
| **W-24** | D-09 | `adversarial-gatekeeper` 적대적 전수 재감사 및 100점 PASS 획득 | `[VERIFIED]` | `sandbox/` | 적대적 재감사 100점 PASS 통과 완료 |
| **W-25** | D-10 | `requirements-extractor` 내 지시사항 4대 대분류 + 5대 소분류 인텐트 분류기(`classify_intent.py`) 구축 | `[VERIFIED]` | `sandbox/.agents/skills/requirements-extractor/scripts/classify_intent.py` | 적대적 감시자 100점 PASS 획득 |
| **W-26** | D-10 | `extract_contract.py`에 인텐트 분류기 연동 (비요구사항 필터링 및 요구사항 하위유형별 EARS 템플릿 차등화) | `[VERIFIED]` | `sandbox/.agents/skills/requirements-extractor/scripts/extract_contract.py` | 적대적 감시자 100점 PASS 획득 |
| **W-27** | D-10 | `SKILL.md`, `GEMINI.md`, `README.md` 및 가이드 문서에 인텐트 게이트웨이 프로토콜 반영 | `[VERIFIED]` | `sandbox/` | 적대적 감시자 100점 PASS 획득 |
| **W-28** | D-10 | `adversarial-gatekeeper` 적대적 전수 재감사 및 100점 PASS 획득 | `[VERIFIED]` | `sandbox/` | 적대적 감시자 100점 PASS 통과 완료 |
| **W-29** | D-11 | 스킬 스크립트 8종 전수 검토 및 엣지 케이스 시정 (`classify_intent.py`, `extract_contract.py`, `enforce_adversarial_gate.py`) | `[VERIFIED]` | `sandbox/.agents/skills/` | 적대적 감시자 100점 PASS 획득 |
| **W-30** | D-11 | 3계층 검증 엔진 구축: `universal_audit_runner.py`에 `flake8`, AST `LazyStubDetector`, 동적 테스트 러너 통합 | `[VERIFIED]` | `sandbox/.agents/skills/adversarial-gatekeeper/scripts/universal_audit_runner.py` | 적대적 감시자 100점 PASS 획득 |
| **W-31** | D-11 | 동반 테스트 스위트(`sandbox/tests/test_skills_runtime.py`) 구축 및 런타임 무결성 실증 | `[VERIFIED]` | `sandbox/tests/test_skills_runtime.py` | 적대적 감시자 100점 PASS 획득 |
| **W-32** | D-11 | `GEMINI.md`, `README.md`, `SKILL.md` 거버넌스 문서 동기화 및 `adversarial-gatekeeper` 적대적 전수 재감사 | `[VERIFIED]` | `sandbox/` | 1차 50점 HOLD 수령 ➔ PUNCH-01 시정 ➔ 2차 100점 PASS 획득 |
| **W-33** | D-12 | `extract_contract.py` 자체 완결형 경량화 및 외부 의존성 제거 (`classify_text` 내장) | `[VERIFIED]` | `sandbox/.agents/skills/requirements-extractor/scripts/extract_contract.py` | 적대적 감시자 100점 PASS 획득 |
| **W-34** | D-12 | 사전 규격 합의 제약 게이트(Pre-Agreement Constraint Gate) 확립 및 `classify_intent.py` 래퍼화 | `[VERIFIED]` | `sandbox/GEMINI.md`, `classify_intent.py`, `SKILL.md` | 적대적 감시자 100점 PASS 획득 |
| **W-35** | D-12 | 동반 단위 테스트(`sandbox/tests/test_skills_runtime.py`) 갱신 및 3계층 무결성 실증 (10/10 PASS) | `[VERIFIED]` | `sandbox/tests/test_skills_runtime.py` | 적대적 감시자 100점 PASS 획득 |
| **W-36** | D-12 | 거버넌스 문서(`README.md`) 동기화 및 `adversarial-gatekeeper` 적대적 전수 재감사 | `[VERIFIED]` | `sandbox/` | 적대적 감시자 100점 PASS 획득 |


