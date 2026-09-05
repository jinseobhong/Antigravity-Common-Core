# EARS (Easy Approach to Requirements Syntax) Guide

본 문서는 엔터프라이즈 환경에서 모호한 자연어 요구사항을 제거하기 위한 EARS 공식 작성 가이드입니다.

---

## 1. 5대 EARS 패턴

EARS(Easy Approach to Requirements Syntax)는 시스템 요구사항을 체계적으로 분류하고 검증하기 위해 다음 5가지 표준 구문 패턴을 제공합니다.

### 1. 일반 요건 (Ubiquitous Requirements)
- **용도**: 이벤트나 상태와 무관하게 시스템이 상시 만족해야 하는 기본 동작.
- **문법**: The `<system name>` SHALL `<system response>`.
- **예시**: "시스템은 모든 출력 텍스트를 UTF-8 인코딩으로 인코딩해야 한다(SHALL)."

### 2. 이벤트 구동 요건 (Event-Driven Requirements)
- **용도**: 특정 트리거/입력이 발생하는 순간 수행되어야 하는 동작.
- **문법**: WHEN `<trigger>`, the `<system name>` SHALL `<system response>`.
- **예시**: "사용자가 `--summary` 인자를 전달했을 때(WHEN), 시스템은 변경 요약 통계를 출력해야 한다(SHALL)."

### 3. 상태 구동 요건 (State-Driven Requirements)
- **용도**: 시스템이 특정 모드나 상태에 머무는 동안 유지해야 하는 동작.
- **문법**: WHILE `<in a state>`, the `<system name>` SHALL `<system response>`.
- **예시**: "격리 샌드박스 모드에서 동작하는 동안(WHILE), 시스템은 루트 디렉토리 직접 쓰기를 원천 차단해야 한다(SHALL)."

### 4. 원치 않는 동작/장애 요건 (Unwanted Behavior / Error Requirements)
- **용도**: 입력 오류, 권한 오류, 런타임 예외 발생 시의 안전한 방어 동작.
- **문법**: IF `<error/exception>`, THEN the `<system name>` SHALL `<system response>`.
- **예시**: "만약 대상 부모 디렉토리가 존재하지 않는다면(IF), 시스템은 상위 디렉토리를 선제 생성한 후 파일을 저장해야 한다(THEN SHALL)."

### 5. 선택적 기능 요건 (Optional Feature Requirements)
- **용도**: 특정 설정/플래그가 활성화되었을 때만 수행되는 부가 동작.
- **문법**: WHERE `<feature is included>`, the `<system name>` SHALL `<system response>`.
- **예시**: "`--output-patch` 옵션이 제공되었을 때(WHERE), 시스템은 통합 diff를 지정된 파일로 저장해야 한다(SHALL)."
