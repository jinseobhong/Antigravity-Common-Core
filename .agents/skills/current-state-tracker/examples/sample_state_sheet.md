# 📊 작업 상황표 (STATE.md)

본 문서는 샌드박스 내부의 현재 작업 진행 상황 및 단계별 체크포인트를 추적하는 공식 상황표 예시입니다.

---

## 🧭 작업 나침반 (Breadcrumbs)
- **📍 마지막 완료 작업 (Last Action)**: [W-02] DB 접속 비동기 세션 관리자 구현 및 커넥션 핑 검증 완료 ([STAGED] ➔ [VERIFIED])
- **🎯 현재 활성 목표 (Active Target)**: [W-03] JWT 토큰 발급 및 만료 검증 로직 구현 ([PLANNED] ➔ [IN_PROGRESS])
- **⏭️ 직후 예정 단계 (Next Step)**: [W-03] 로컬 단위 테스트 작성 및 정적 분석 통과 후 [VERIFIED] 전이

---

## 📥 사용자 원문 지시 백로그 (User Directives)
- **D-01**: "DB 세션 관리자와 JWT 토큰 발급 기능을 구현해줘." ➔ 담당 태스크: `W-01`, `W-02`, `W-03`
- **D-02**: "로그인 API 엔드포인트와 카카오 간편로그인 추가해줘." ➔ 담당 태스크: `W-04`, `W-05`

---

## 📌 작업 상태 매트릭스 (Task Matrix)
| 작업 ID | 매핑 지시 | 작업 명세 | 상태 딱지 | 산출물 위치 (Sandbox Path) | 다음 액션 |
| :---: | :---: | :--- | :---: | :--- | :--- |
| **W-01** | D-01 | 데이터 모델 및 Pydantic 스키마 정의 | `[VERIFIED]` | `sandbox/src/models.py` | 문법 검증 완료 |
| **W-02** | D-01 | DB 접속 비동기 세션 풀 관리자 | `[VERIFIED]` | `sandbox/src/database.py` | 커넥션 핑 테스트 완료 |
| **W-03** | D-01 | JWT 토큰 발급 및 만료 검증 | `[IN_PROGRESS]` | `sandbox/src/auth.py` | 만료 시간 검증 로직 작성 중 |
| **W-04** | D-02 | 이메일/비밀번호 로그인 API 라우트 | `[BLOCKED]` | `sandbox/src/routes/auth.py` | W-03 완료 후 착수 예정 (의존성 대기) |
| **W-05** | D-02 | 카카오 소셜 간편로그인 연동 | `[REQUESTED]` | *(미정)* | 사용자 지시 접수 완료 (계획 미착수) |
