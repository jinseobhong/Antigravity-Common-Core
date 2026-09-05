# Code Review Gatekeeper Rubric & Evaluation Standards

본 문서는 자율 품질 게이트(Quality Gate) 심사관이 작업자(Worker) 에이전트의 산출물을 평가할 때 적용하는 정량적 평가 기준 및 결함 분류 규격서입니다.

---

## 1. 구현 충실도 및 명세 준수 (Fidelity & Conformance) - 35점

| 평가 항목 | 감점 배점 | 판정 기준 및 위반 정의 |
| :--- | :---: | :--- |
| **미완성 로직 및 플레이스홀더 잔재**<br>*(Unresolved Stubs & Placeholders)* | **건당 -15점 / Hard Gate** | 소스코드 내 `TODO`, `FIXME`, `pass`, `NotImplementedError`, 임시 모의(Mock) 객체 및 하드코딩된 불리언 반환값 잔존 시 불합격 |
| **요구 명세 누락**<br>*(Specification Omission)* | **건당 -10점** | 사용자 프롬프트 또는 인터페이스 계약에 명시된 기능적 요구사항(페이징, 정렬, 유효성 검증, 필터링 등)의 누락 |
| **경계 조건 및 예외 입력 검증 결여**<br>*(Boundary & Exceptional Input Handling)* | **건당 -5~-10점** | `null`, `undefined`, 빈 컬렉션, 경계값(Boundary values)에 대한 유효성 검증 부재로 인한 런타임 결함 가능성 |
| **비정상 흐름 처리 결여**<br>*(Failure Flow Neglect)* | **건당 -5점** | 원본 예외 스택 추적 소실, 원인 파악이 불가능한 제네릭 에러 메시지 반환, 외부 연동 실패 시의 폴백 로직 부재 |

---

## 2. 제어 흐름 및 인지 복잡도 (Control Flow & Cognitive Complexity) - 25점

| 평가 항목 | 감점 배점 | 판정 기준 및 위반 정의 |
| :--- | :---: | :--- |
| **과도한 제어 블록 중첩**<br>*(Excessive Nesting)* | **건당 -8~-10점** | 3단계 이상의 제어문(`if/else`, 루프) 중첩. 보호 구문(Guard Clauses / Early Return) 미적용으로 인한 가독성 저하 |
| **중복 구현 및 DRY 원칙 위반**<br>*(Duplication / DRY Violation)* | **건당 -10점** | 5라인 이상의 구조적 유사성을 가진 코드 블록이 공통 모듈로 추상화되지 않고 2개 이상의 위치에 중복 정의됨 |
| **리터럴 상수 미추출**<br>*(Unextracted Literal Constants)* | **개당 -2~-5점** | 시간 간격, 임계값, 상태 문자열 등 비즈니스 의미를 갖는 리터럴이 명명된 상수(`UPPER_SNAKE_CASE`)로 정의되지 않음 |

---

## 3. 모듈화 및 상태 무결성 (Modularity & State Integrity) - 25점

| 평가 항목 | 감점 배점 | 판정 기준 및 위반 정의 |
| :--- | :---: | :--- |
| **인자 직접 변이로 인한 부수 효과**<br>*(In-place Parameter Mutation)* | **건당 -10점** | 함수 파라미터로 전달된 객체 또는 컬렉션을 직접 변이하여 호출자 컨텍스트에 예측할 수 없는 부수 효과 초래 |
| **단일 책임 원칙 위반**<br>*(Single Responsibility Violation)* | **건당 -10점** | 단일 함수가 40라인을 초과하며 데이터 파싱, 유효성 검증, 비즈니스 연산, 영속성 작업을 동시에 수행 |
| **불명확한 식별자 명명**<br>*(Ambiguous Domain Naming)* | **건당 -2점** | `tmp`, `data2`, `chk`, `val` 등 도메인 의미를 유추할 수 없는 불명확한 약어 및 식별자 사용 |

---

## 4. 코드 위생 및 런타임 신뢰성 (Hygiene & Runtime Reliability) - 15점

| 평가 항목 | 감점 배점 | 판정 기준 및 위반 정의 |
| :--- | :---: | :--- |
| **비활성 코드 및 디버그 잔재**<br>*(Dead Code & Debug Artifacts)* | **건당 -5점** | 주석 처리된 과거 코드 블록 잔존, 디버깅 목적의 로깅 호출(`console.log`, `print`) 방치 |
| **예외 은폐**<br>*(Suppressed Exceptions)* | **건당 -5점** | `except: pass` 또는 비어있는 `catch` 블록을 사용하여 런타임 예외를 무시하거나 은폐하는 안티패턴 |
| **정적 타입 시스템 우회**<br>*(Type System Circumvention)* | **건당 -10점 / Hard Gate** | 정적 타입 안전성을 고의로 무력화하는 무분별한 `any` 또는 `as any` 타입 캐스팅 적용 |
