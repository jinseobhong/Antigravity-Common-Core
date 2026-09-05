# Enterprise Non-Functional Requirements (NFR) Checklist

엔터프라이즈 환경에서 적대적 감시자가 점검하는 6대 핵심 비기능 요건 체크리스트입니다.

---

## 1. 멱등성 (Idempotency)
- [ ] 동일한 CLI 명령어나 스크립트가 2회 이상 연속 실행되어도 파일 손상이나 중복 추가가 발생하지 않는가?
- [ ] 반복 실행 후 디스크 및 상태표의 최종 상태가 동일하게 수렴하는가?

## 2. 시간 제한 및 기한 (Timeouts & Deadlines)
- [ ] 외부 프로세스(`subprocess.run`) 실행 시 명시적 `timeout` 파라미터가 설정되어 있는가?
- [ ] 무한 대기(Hang)를 유발할 수 있는 블로킹 I/O 호출이 존재하는가?

## 3. 예외 격리 및 정상 복구 (Fault Isolation & Graceful Degradation)
- [ ] 광범위한 `except Exception: pass`로 예외를 은폐하지 않고 구체적인 예외 타입을 처리하는가?
- [ ] 파일 미존재, 권한 부족, 디코딩 오류 발생 시 명확한 에러 메시지와 함께 비정상 종료를 방지하는가?

## 4. 플랫폼 및 환경 안전성 (Environment Robustness)
- [ ] Windows 환경에서 CP949 / UTF-8 인코딩 충돌 없이 표준 출력이 보호되는가?
- [ ] 경로 처리 시 OS 독립적인 `pathlib.Path`를 사용하여 슬래시/백슬래시 호환성을 확보했는가?

## 5. 보안 및 위생 (Zero Secret Leak)
- [ ] API 키, 개인 토큰, 비밀번호 등의 자격 증명이 평문으로 하드코딩되거나 로그에 노출되지 않는가?

## 6. 스텁 및 미완성 코드 방지 (Zero Stubbing)
- [ ] `TODO`, `FIXME`, `pass`, `NotImplementedError`, 임시 하드코딩 리턴값이 소스코드 내에 방치되지 않았는가?
