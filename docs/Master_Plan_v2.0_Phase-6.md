ocal Finder X
Phase 6 — Implementation Plan & Sprint Backlog

(v2.0 Greenfield Rebuild · Authoritative Document)

0. 문서 목적 및 적용 범위
0.1 목적

본 문서는 v2.0 구현을 **개발 실행 가능한 단위(이슈/PR)**로 분해하고,
각 단위를 의존성 순서대로 고정한다.

0.2 적용 범위

코드베이스 초기화부터 패키징 전 단계까지

Storage/Core/UI/Connectors/Security 전부 포함

Free/Pro 라이선스(오프라인 키) 최소 구현 포함

1. Phase 6에서 고정되는 결정 사항 (Non-Negotiable)

구현은 반드시 Storage → Core(Index) → Core(Search) → UI → Pro Connectors 순서를 따른다.

UI는 SearchResponse를 그대로 렌더링한다(중간 가공 금지).

인덱싱/검색은 UI 스레드에서 실행 금지.

“동작하는 것을 빠르게”가 아니라 PRD·Phase 문서 정합성이 우선이다.

2. In-Scope / Out-of-Scope
2.1 In-Scope

GitHub 이슈/PR 단위 분해

Acceptance Criteria(AC) 명세

테스트/검증 요건 포함

2.2 Out-of-Scope

실제 일정/리소스(사람/기간) 산정

디자인 픽셀 퍼펙트

3. 리포지토리 초기 구조 (PR#0)
PR#0: Repo Skeleton & Tooling Baseline

목적

Phase 1 구조대로 디렉토리/모듈 뼈대 생성

개발 환경 고정

생성/수정

/src 폴더 구조 생성(Phase 1 기준)

pyproject.toml 또는 requirements.txt 고정

ruff/black(선택) 설정

pytest 설정

기본 실행 엔트리포인트(빈 창)

AC

python -m src.app.main 실행 시 빈 앱 창 표시

테스트 러너 실행 가능

테스트

smoke test 1개(앱 실행만)

4. Sprint 1 — Storage Layer (필수 기반)

UI/검색 이전에 “저장·복구·증분 상태”가 반드시 먼저 완성되어야 함.

PR#1: App Data Paths & Settings

src/config/paths.py: OS별 앱 데이터 경로 결정

src/config/settings.py: settings.json load/save

AC

Windows/macOS에서 앱 데이터 경로가 안정적으로 생성됨

settings.json 읽기/쓰기 성공

PR#2: Data Schemas (DTO/Models)

Phase 2 스키마 그대로 Python dataclass/Pydantic으로 정의

FileRecord, ChunkRecord, Evidence, SearchResponse 등

AC

필드 누락 시 생성 실패(명시적 validation)

schema_version 기본값 “2.0”

테스트

DTO 생성/직렬화 단위 테스트

PR#3: Manifest Store (Incremental Indexing Core)

src/storage/manifest.py: manifest.json load/save

fingerprint 비교 함수 구현

AC

변경 없음 → skip

변경 있음 → reindex 대상

삭제 파일 → manifest에서 제거 대상 반환

테스트

가짜 파일 메타로 증분 규칙 검증

PR#4: LanceDB Setup & Schema

src/storage/lancedb_store.py

LanceDB connect & Table create (Schema Definition)

AC

DB 폴더 생성 및 연결 성공

Schema대로 Table 생성 확인

PR#5: VectorStore Adapter

src/storage/vector_store.py

LanceDB wrapper (add, search, delete)

AC

file_id로 chunk vector 추가/삭제 가능

metadata 필터링 쿼리 동작 확인

PR#6: BM25Store (Persistent)

src/storage/bm25_store.py

토큰 리스트 기반 BM25 인덱스 생성/저장/로드

AC

앱 재시작 후 BM25 인덱스 재사용

토큰이 없는 문서는 검색 대상 제외

5. Sprint 2 — Indexing Core (Content + Metadata-Only)
PR#7: File Enumeration + Filtering

폴더 트리(선택된 루트)에서 파일 목록 생성

임시 파일(~$, .tmp) 제외

AC

1개 폴더 선택 시 하위 파일 목록 정확히 생성

제외 규칙 적용됨

PR#8: File Type Classifier

확장자 기반 content_indexed 결정(Phase 3)

OTHER는 metadata-only

AC

지원 확장자는 content_indexed=true

그 외는 false

PR#9: Extractors (v2.0 범위)

docx, pptx, xlsx, pdf, md 추출기 구현(Phase 3 규칙)

AC

샘플 파일에서 텍스트 추출 성공

실패 시 downgrade 로직을 상위 파이프라인이 처리 가능

테스트

fixtures 샘플 파일로 파서 단위 테스트

PR#10: Structural Chunker

파일 타입별 청킹 규칙 구현(Phase 3)

위치 메타데이터 필수

AC

PDF: page metadata 존재

PPT: slide metadata 존재

Excel: sheet/row_range 존재

Word/MD: header_path 존재(없으면 null 허용)

PR#11: Tokenizer (Kiwi + English)

src/core/tokenizer.py

Kiwi 설치 가능 환경에서 한국어 토큰 추출

설치 불가/오류 시 fallback(단순 split) — 단, 반드시 경고 로그

AC

한국어 쿼리/텍스트 토큰이 비어있지 않음(일반 문장 기준)

예외가 나도 인덱싱 전체 중단 ❌

PR#12: Embedding Model Wrapper

SentenceTransformer 래퍼

디바이스 자동 선택(CUDA/MPS/CPU)

AC

embedding normalize=True

모델 로딩 실패 시 인덱싱은 metadata-only로 downgrade 처리 가능

PR#13: Indexing Orchestrator (Controller)

src/core/indexer.py

manifest 기반 증분 인덱싱

FileRecord/ChunkRecord 생성

Storage stores에 기록

AC

변경 없는 파일 skip

변경 파일 재인덱싱(기존 chunk 삭제 후 재생성)

인덱싱 완료 후 결과 요약 생성

6. Sprint 3 — Search Core (Hybrid + Evidence)
PR#14: Dense Retriever

query embedding 생성

VectorStore topN chunk 검색

AC

topN 반환, score 0~1

PR#15: Lexical Retriever (BM25)

query tokens 생성

BM25 topN

metadata-only 파일은 file-level tokens로 검색 가능

AC

metadata-only가 파일명 검색으로 결과에 포함됨

PR#16: RRF Fusion (File-level)

Phase 4 수식 및 k=60 고정

chunk 결과를 file_id로 묶어 rank 생성

AC

Dense만/lexical만 있어도 동작

PR#17: File Aggregator + Score Decay

file_score 공식 구현(Phase 4)

metadata-only 0.4 감쇠

AC

감쇠는 aggregation 이후 적용

PR#18: Evidence Builder

file별 top evidences 선택(Phase 4)

snippet 200~500 chars + highlight

AC

evidence 중복 위치 최소화

metadata-only는 evidence=[]

템플릿 기반 summary 생성

PR#19: SearchEngine (End-to-End)

QueryProcessor → retrievers → fusion → aggregator → evidence → SearchResponse

AC

UI가 별도 가공 없이 결과 렌더 가능한 SearchResponse 반환

테스트

통합 테스트: 샘플 인덱스 생성 후 검색 결과 검증

7. Sprint 4 — UI Implementation (Global Sidebar + Pages)
PR#20: Main Window + Global Sidebar Routing

Search/Indexing/About/MyPage 전환 구현

AC

라우팅 상태 유지

Search 기본 진입

PR#21: Search Page (3-Panel Skeleton)

좌/중/우 레이아웃 고정

Right 패널 입력 이벤트 연결(검색 실행)

AC

검색 실행 시 로딩 표시

완료 시 Left 리스트 업데이트

PR#22: Left Panel (Results List)

FileHit 리스트 렌더

content availability 배지 표시

클릭 시 Center 업데이트

AC

metadata-only 클릭 시 Center가 안내 카드 표시

PR#23: Center Panel (Evidence Cards)

Evidence 카드 리스트

preview 영역

Copy/Ask 버튼 이벤트

AC

Ask 클릭 시 Right 입력창에 프리필

PR#24: Right Panel (Chat-like UX)

히스토리 표시

모드 토글(FAST/SMART/ASSIST)

필터 팝오버(파일타입/기간/폴더)

AC

모드/필터가 SearchEngine 호출 파라미터로 전달됨

PR#25: Indexing Page

파일 타입 필터

폴더 트리 체크 UI

인덱싱 실행 버튼/진행 표시/결과 요약

AC

진행 중 cancel 가능(안전 종료)

완료 후 요약 숫자 표기

PR#26: About Page

기존 About 내용 이관(정적)
AC

내용 변경 없음

PR#27: My Page

라이선스 입력

Free/Pro 상태 표시

스코프 요약 표시

AC

잘못된 키 입력 시 invalid 상태 표시

8. Sprint 5 — Pro Scope & Security Polish
PR#28: Outlook Connector (Graph API)

Azure App 인증 (OAuth 2.0 PKCE)

MS Graph API Client 구현 (Users, MailFolders, Messages)

AC

로그인 창 팝업 및 토큰 획득

내 메일함 목록 조회 성공

PR#29: OneDrive/SharePoint Connector (Graph API)

Graph API drive/root/children 탐색 구현

AC

OneDrive 파일 목록 조회 및 텍스트 추출 가능

PR#30: Google Drive Button (UI Only)

버튼/상태 UI만 제공

클릭 시 “v2.1 예정” 안내

AC

실제 연결/인덱싱 없음

PR#31: PII Masking (Display Stage)

Center Panel snippet / Right 응답 출력 직전 마스킹

정책: 전화/이메일/주민번호

AC

기본 ON

설정에서 해제(옵션) 가능하되 v2.0 기본 OFF로 노출(=해제 기능 숨김 가능)

PR#32: Audit Log (Pro)

검색 이벤트 JSONL 기록

AC

query는 hash로 저장 가능

날짜별 로테이션

9. Sprint 6 — Packaging & Offline Verification
PR#33: Packaging Scripts (PyInstaller)

Windows/macOS 빌드 스크립트

오프라인 모델 번들링 정책 문서화

AC

인터넷 차단 환경에서 실행 가능

첫 실행 시 모델 경로 확인

PR#34: Offline Guardrail

네트워크 호출 차단/탐지(옵션)

“외부 통신 없음” self-check

AC

테스트에서 외부 호출 시 실패 처리 가능(개발 모드)

10. Definition of Done (전체 v2.0)

Global Sidebar 4 페이지 동작

Search 3-Panel 동작 + Explainable evidence

Indexing 페이지에서:

파일 타입 필터

폴더 트리 선택

인덱싱 실행/진행/요약

Content Indexed + Metadata-Only 결과 통합 노출

Free/Pro 스코프 차별:

기능 동일

대상 범위만 차이

Pro: Outlook export 인덱싱 + Sync folder

런타임 외부 통신 없음

PII 마스킹(디스플레이) 적용

Audit log(Pro) 적용

오프라인 설치/실행 가능

11. 이후 변경 가능 범위
변경 가능

Sprint 내부 작업 재배치(단, 의존성 위반 금지)

UI 문구

변경 불가

Storage → Core → UI 구현 순서

SearchResponse 바인딩 원칙

Free/Pro 차별 원칙