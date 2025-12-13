Local Finder X
Phase 7 — Test Plan, Benchmarking & Release Checklist

(v2.0 Greenfield Rebuild · Authoritative Document)

0. 문서 목적 및 적용 범위
0.1 목적

본 문서는 다음을 명확히 판단하기 위한 기준 문서다.

v2.0이 기능적으로 완성되었는가

검색 품질이 기존 대비 의미 있게 개선되었는가

“100% 로컬 / 오프라인” 약속이 실제 보장되는가

Free / Pro 정책이 일관되게 구현되었는가

0.2 적용 범위

단위 테스트(Unit)

통합 테스트(Integration)

검색 품질 벤치마크(Quality)

성능 벤치마크(Performance)

보안/오프라인 검증(Security)

릴리즈 승인 체크리스트

1. Phase 7에서 고정되는 결정 사항 (Non-Negotiable)

자동 테스트 통과 없이는 릴리즈 불가

검색 품질은 정성 + 정량 지표를 모두 만족해야 함

오프라인 검증은 “네트워크 차단 환경”에서 수행

Free/Pro 차이는 검색 결과 품질이 아니라 범위만 달라야 함

실패한 항목은 “Known Issue”로 릴리즈 불가 (v2.0 기준)

2. 테스트 데이터셋 규격 (Authoritative)
2.1 테스트 데이터셋 목적

실제 타깃 고객(지식노동자)의 현실적인 파일 환경을 재현

2.2 필수 데이터 구성
문서 유형

Word: 20개 (버전명 포함: v0.1, v0.2, final 등)

Excel: 10개 (테이블 구조 다양)

PPT: 10개 (슬라이드 5~30장)

PDF: 10개 (텍스트 기반)

Markdown: 5개

기타 파일(이미지/zip 등): 20개 (metadata-only 검증용)

이메일(Pro 테스트용)

Outlook export:

메일 50개

첨부파일 포함 10개

2.3 폴더 구조 (필수)

다층 구조(깊이 ≥ 4)

동일 파일명, 다른 경로 존재

날짜/버전 혼합 구조

3. Unit Test Plan
3.1 Storage Layer
대상	검증 항목
Manifest	변경/삭제/신규 정확 판별
FileStore	재시작 후 데이터 유지
ChunkStore	file_id 기반 조회
BM25Store	저장/로드 후 동일 검색 결과

통과 기준

모든 단위 테스트 pass

파일 시스템 깨끗이 삭제 후 재생성 가능

3.2 Indexing Core
대상	검증
File Enumerator	제외 규칙 적용
Classifier	content vs metadata 정확
Extractors	파일 타입별 정상 추출
Chunker	위치 메타데이터 존재
Tokenizer	빈 토큰 발생률 < 5%
Embedder	실패 시 downgrade 정상
3.3 Search Core
대상	검증
Dense Retriever	topN 반환
BM25 Retriever	metadata-only 포함
RRF	Dense/Lexical 단독 시도 정상
Aggregator	score 계산 공식 일치
Evidence Builder	최대 개수/중복 방지
4. Integration Test Plan (End-to-End)
4.1 인덱싱 → 검색 플로우

시나리오

폴더 선택

인덱싱 실행

검색 쿼리 입력

결과 UI 표시

파일 열기

검증

UI 프리징 ❌

인덱싱/검색 중 취소 가능

검색 결과 클릭 시 Center Panel 정상 업데이트

4.2 Metadata-Only 파일 시나리오

검증

파일명 검색 시 결과 포함

Evidence 없음 안내 표시

검색 점수 감쇠 적용

4.3 Pro 스코프 시나리오
항목	Free	Pro
로컬 파일	⭕	⭕
Outlook	❌	⭕
OneDrive Sync	❌	⭕
검색 품질	동일	동일
5. 검색 품질 벤치마크 (Quality)
5.1 정성 평가 (Human-in-the-loop)

질문 세트 예시

“작년 매출 정리한 파일”

“OO 프로젝트 초안”

“비용 늘어난 이유 설명한 문서”

“메일로 받은 계약서”

평가 기준

Top 3에 정답 파일 포함 여부

Evidence가 “왜 맞는지” 설명 가능한가

5.2 정량 지표 (필수)
지표	목표
Recall@5	≥ 0.85
MRR@10	≥ 0.75
Evidence Hit Rate	≥ 0.8
Metadata-only False Positive	≤ 10%

기준 미달 시 릴리즈 ❌

6. 성능 벤치마크 (Performance)
6.1 테스트 환경 기준

CPU: 일반 노트북급 (i5/M1)

RAM: 16GB

디스크: SSD

6.2 성능 목표
항목	목표
인덱싱 속도	≥ 300 files / 5 min
검색 응답	< 1.5s (SMART)
FAST 모드	< 0.7s
UI 프레임 드랍	없음
7. 오프라인 / 보안 검증 (Critical)
7.1 오프라인 검증

방법

네트워크 완전 차단

DNS 차단

프록시 강제 설정

검증

앱 정상 실행

검색/인덱싱 정상

외부 호출 로그 0건

7.2 PII 마스킹 검증
항목	기대
전화번호	마스킹
이메일	마스킹
주민번호	마스킹
파일 열기	원본 그대로
7.3 Audit Log (Pro)

검색 이벤트 기록 여부

query hash 처리

날짜별 파일 분리

8. 회귀 테스트 (Regression)
필수 시나리오

재인덱싱 후 검색 결과 동일

파일 삭제 후 결과 제거

settings.json 삭제 후 자동 복구

라이선스 변경 후 UI 상태 즉시 반영

9. Release Checklist (Gate)
9.1 기술 체크리스트 (모두 ⭕)

 Unit Test 100% Pass

 Integration Test Pass

 Quality Metrics 충족

 Offline 검증 완료

 Free/Pro 스코프 일관성 확인

 크래시 0건

9.2 제품 체크리스트

 About 문구 정확

 Pro 안내 문구 명확

 검색 결과 Explainable

 “왜 이 파일인가” 이해 가능

9.3 운영 체크리스트

 설치/실행 가이드 최신

 FAQ 업데이트

 Known Issue 없음(v2.0 기준)

10. v2.0 릴리즈 승인 기준 (Final)

v2.0은 아래 조건을 모두 만족할 때만 릴리즈 가능하다.

Phase 1–7 문서와 코드 100% 정합

테스트/벤치 전부 통과

오프라인 약속 기술적으로 증명

Free/Pro 차별 정책 혼선 없음

“이 제품은 신뢰할 수 있다”는 내부 합의

11. 이후 변경 가능 범위
변경 가능

성능 목표 수치(하향 ❌, 상향 ⭕)

테스트 데이터 규모 증가

변경 불가

품질 지표 정의

오프라인 검증 기준

릴리즈 게이트 조건