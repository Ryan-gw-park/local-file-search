Local Finder X
Phase 3 — Indexing Pipeline & Structural Chunking Design

(v2.0 Greenfield Rebuild · Authoritative Document)

0. 문서 목적 및 적용 범위
0.1 목적

본 문서는 파일 스캔 → 분류 → 텍스트 추출 → 구조적 청킹 → 토큰/임베딩 생성 → 저장까지
인덱싱 전체 파이프라인의 “행동 규칙”을 완전히 고정한다.

이 문서는 다음 질문에 단일 답을 제공해야 한다.

“이 파일은 왜 content indexed 인가?”

“이 문서는 왜 이 단위로 잘렸는가?”

“이 chunk는 왜 이 메타데이터를 가지는가?”

0.2 적용 범위

Local File Indexing

Outlook (Graph API) Indexing

Content Indexed / Metadata-Only 분기

구조 기반 청킹 규칙(v2.0 범위)

1. Phase 3에서 고정되는 결정 사항 (Non-Negotiable)

파일 분류(Content vs Metadata-Only)는 인덱싱 초입에서 단 한 번 결정

Chunking은 파일 타입별로 다르게 동작

모든 Chunk는 “위치 메타데이터”를 반드시 가진다

구조 정보가 없을 경우에만 길이 기반 청킹으로 fallback

인덱싱 실패는 downgrade(콘텐츠 → 메타데이터)로 처리, 중단 금지

2. In-Scope / Out-of-Scope
2.1 In-Scope

파일 스캔 규칙

파일 타입 판별

텍스트 추출 규칙

구조적 청킹 규칙

토큰화/임베딩 생성 시점

인덱싱 실패 처리

2.2 Out-of-Scope

검색 알고리즘

UI 렌더링

성능 튜닝 파라미터

3. 인덱싱 파이프라인 전체 흐름 (Authoritative)
[File Enumerator]
        │
        ▼
[File Type Classifier]
        │
        ├─ Content Indexed
        │      │
        │      ▼
        │  [Text Extractor]
        │      │
        │      ▼
        │  [Structural Chunker]
        │      │
        │      ▼
        │  [Tokenizer + Embedder]
        │      │
        │      ▼
        │  [ChunkRecord Builder]
        │
        └─ Metadata Only
               │
               ▼
        [FileRecord Builder]

4. 파일 스캔 및 분류 규칙
4.1 파일 스캔 대상

사용자가 Indexing 화면에서 선택한 폴더 트리

숨김 파일:

기본 제외

설정에서 포함 가능(v2.0 기본 OFF)

임시 파일:

~$, .tmp 접두사 → 항상 제외

4.2 Content Indexed 파일 판별 규칙 (강제)
조건	결과
확장자가 지원 콘텐츠 유형	Content Indexed
Outlook 이메일(본문/첨부)	Content Indexed
그 외 파일	Metadata-Only

Content Indexed 여부는 이 단계에서만 결정되며,
이후 파이프라인에서 변경 ❌

5. 파일 타입별 텍스트 추출 규칙
5.1 공통 규칙

텍스트 추출 실패 시:

해당 파일은 content_indexed=false 로 downgrade

FileRecord는 유지

바이너리/이미지 OCR ❌ (v2.0 제외)

5.2 Word (.docx)

추출 대상:

본문 paragraph

Heading 스타일(level 1~4)

추출 결과:

(header_path, paragraph_text) 튜플 리스트

5.3 PowerPoint (.pptx)

추출 대상:

슬라이드 제목

슬라이드 본문 텍스트 박스

규칙:

슬라이드 단위로 결합

제목은 항상 본문 앞에 prepend

5.4 Excel (.xlsx)

추출 대상:

시트별 상위 N행 (기본 50)

처리 방식:

DataFrame → Markdown Table

규칙:

NaN → ""

열 수 30 초과 시 오른쪽 열 truncate

Footer:

(Table truncated: total rows = X) 명시

5.5 PDF (.pdf)

추출 단위:

페이지 단위

규칙:

페이지 번호 유지 필수

페이지 텍스트 없을 경우 skip

5.6 Markdown (.md)

추출 대상:

Markdown header hierarchy

결과:

header_path 기반 구조 유지

5.7 Outlook Email (Pro)

추출 대상 (via Graph API):

Subject

Body (HTML -> Text)

첨부파일(지원 확장자)

Email 본문은 하나의 document로 처리

metadata:

from, to, date, subject

6. 구조적 청킹 규칙 (Core of Phase 3)
6.1 공통 Chunking 규칙

최대 길이: 1000 chars

Overlap: 100 chars

Chunk index는 파일 내 순서 기준

6.2 파일 타입별 Chunking
Word / Markdown

header_path 변경 시 새로운 chunk 시작

header_path 유지하며 길이 기준 분할

PowerPoint

슬라이드 1개 = 최소 1 chunk

길이 초과 시 슬라이드 내부에서 분할

metadata:

slide_number

slide_title

Excel

시트 1개 = 1 chunk

시트 길이 초과 시 row_range 기준 분할

metadata:

sheet_name

row_range

PDF

페이지 1개 = 최소 1 chunk

길이 초과 시 페이지 내부 분할

metadata:

page_number

Email

본문 전체 1 chunk

길이 초과 시 문단 기준 분할

7. Tokenization & Embedding 생성 시점
7.1 Tokenization

Chunk 단위로 수행

한국어:

Kiwi 사용

NNG, NNP, SL, SN

영문:

lowercase

length ≥ 2

7.2 Embedding

Chunk 생성 직후 수행

실패 시:

해당 Chunk 폐기

File 전체 downgrade ❌ (다른 chunk는 유지)

8. ChunkRecord 생성 규칙 (재확인)

모든 Chunk는 반드시:

file_id

chunk_index

metadata(location)

tokens

embedding

누락 필드 발생 시:

해당 Chunk 폐기

오류 로그 기록

9. Metadata-Only 파일 처리 (재확인)

Chunk 생성 ❌

FileRecord만 생성

인덱싱 완료 상태로 처리

검색 시:

file-level lexical match만 참여

score 감쇠 적용(Phase 2 규칙)

10. 오류 처리 및 복구 전략
상황	처리
단일 파일 실패	스킵 + downgrade
단일 Chunk 실패	Chunk 폐기
토큰화 실패	해당 Chunk 폐기
디스크 쓰기 실패	인덱싱 중단 + 사용자 알림
11. Phase 3 완료 기준 (DoD)

Phase 3은 아래가 모두 충족되어야 완료다.

모든 파일 타입별 추출/청킹 규칙이 문서화됨

downgrade 규칙이 명확

모든 Chunk에 위치 메타데이터 존재

인덱싱 파이프라인을 코드로 바로 옮길 수 있음

“왜 이 chunk가 존재하는가?”를 문서로 설명 가능

12. 이후 변경 가능 범위
변경 가능

Chunk size / overlap 수치

Excel 상위 행 수

Kiwi 토큰 태그 범위

변경 불가

파일 타입별 구조 청킹 전략

Content vs Metadata 분기 시점

downgrade 정책