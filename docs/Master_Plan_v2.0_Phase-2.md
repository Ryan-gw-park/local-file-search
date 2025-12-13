Local Finder X
Phase 2 — Data Model & Storage Design

(v2.0 Greenfield Rebuild · Authoritative Document)

0. 문서 목적 및 적용 범위
0.1 목적

본 문서는 Local Finder X v2.0의 모든 데이터 구조, 저장 포맷, 식별자 규칙, 증분 인덱싱 기준을 정의한다.

이 문서가 고정하는 대상:

모든 레코드 타입의 필드 정의

Content Indexed / Metadata-Only 통합 모델

디스크 저장 구조

인덱스 재사용·마이그레이션 규칙

검색 결과 전달용 DTO 구조

0.2 적용 범위

Indexing Pipeline

Search Pipeline

Storage Layer

UI 바인딩(SearchResponse)

1. Phase 2에서 고정되는 결정 사항 (Non-Negotiable)

모든 파일은 단 하나의 FileRecord로 표현

Content Indexed 여부는 플래그로만 구분

Chunk는 UI에 직접 노출되지 않음

검색 결과는 File 중심, 근거는 Evidence로만 제공

Storage는 LanceDB (Embedded) 사용 (외부 DB 서버 불가)

모든 레코드는 schema_version 필드 필수

2. In-Scope / Out-of-Scope
2.1 In-Scope

데이터 모델 정의

저장 포맷 및 디렉토리 구조

증분 인덱싱 규칙

SearchResponse DTO

2.2 Out-of-Scope

실제 파일 파싱 로직

검색 알고리즘 내부 수식

UI 렌더링 방식

3. 핵심 개념 정의 (Glossary)
용어	정의
FileRecord	파일 1개를 대표하는 최상위 단위
ChunkRecord	Content Indexed 파일의 검색 최소 단위
Evidence	검색 결과의 “왜 나왔는지”를 설명하는 근거
Manifest	인덱싱 상태 및 fingerprint 관리 파일
Schema Version	데이터 구조 변경을 위한 버전 필드
4. 데이터 모델 — 공통 원칙
4.1 공통 규칙 (모든 레코드 적용)

모든 레코드는 불변 ID를 가진다.

모든 레코드는 schema_version 필드를 포함한다.

저장 시 JSON serializable 구조를 유지한다.

시간 필드는 UTC timestamp(float, epoch seconds) 로 통일한다.

5. FileRecord (Authoritative)
5.1 역할

검색 결과의 1급 시민

Content Indexed / Metadata-Only 파일을 모두 표현

모든 Chunk/Evidence의 부모

5.2 FileRecord 스키마
FileRecord {
  "schema_version": "2.0",
  "file_id": "uuid-v4",
  
  "source": "local | outlook | onedrive | sharepoint | gdrive",
  "content_indexed": true | false,

  "path": "/absolute/path/to/file",
  "filename": "budget_q4_final.xlsx",
  "extension": ".xlsx",

  "size_bytes": 123456,
  "created_at": 1700000000.0,
  "modified_at": 1700001234.0,

  "author": "string | null",

  "fingerprint": {
    "size_bytes": 123456,
    "modified_at": 1700001234.0,
    "hash": "optional_sha256"
  },

  "index_stats": {
    "chunk_count": 12,
    "last_indexed_at": 1700002000.0,
    "index_error": null
  }
}

5.3 필드 설명 및 강제 규칙

file_id

생성 시점 단 한 번만 생성

path 변경 시에도 유지 ❌ → path 변경 = 신규 FileRecord

content_indexed

true: ChunkRecord 존재 필수

false: ChunkRecord 절대 생성 ❌

fingerprint

증분 인덱싱의 기준

하나라도 변경 시 재인덱싱 대상

6. ChunkRecord (Content Indexed Only)
6.1 역할

검색의 최소 단위

UI에 직접 노출 ❌

Evidence 생성의 원재료

6.2 ChunkRecord 스키마
ChunkRecord {
  "schema_version": "2.0",
  "chunk_id": "uuid-v4",
  "file_id": "uuid-v4",

  "chunk_index": 3,
  "text": "string",

  "embedding": [float, ...],
  "tokens": ["string", "..."],

  "metadata": {
    "page": 5,
    "slide": null,
    "sheet": "Q4",
    "row_range": "1-20",
    "header_path": ["Budget", "Q4 Adjustments"]
  }
}

6.3 메타데이터 규칙 (파일 타입별)
파일 타입	필수 메타데이터
PDF	page
PPT	slide, slide_title
Excel	sheet, row_range
Word/MD	header_path
Email	subject, date, from
7. Evidence Model (UI 전달 전용)
7.1 역할

“왜 이 파일이 검색 결과인지” 설명

ChunkRecord → UI 안전 모델로 변환

7.2 Evidence 스키마
Evidence {
  "evidence_id": "uuid-v4",
  "file_id": "uuid-v4",

  "summary": "이 부분이 'Q4 예산 조정'과 가장 유사합니다.",
  "snippet": "string (200~500 chars, highlighted)",

  "scores": {
    "final": 0.82,
    "dense": 0.75,
    "lexical": 0.68
  },

  "location": {
    "page": 5,
    "sheet": "Q4",
    "slide": null
  }
}

8. SearchResponse DTO (UI 바인딩용)
8.1 SearchResponse
SearchResponse {
  "query": "string",
  "elapsed_ms": 123,

  "results": [
    {
      "file": FileRecord,
      "score": 0.91,
      "match_type": "semantic | lexical | hybrid",
      "content_available": true | false,
      "evidences": [Evidence, ...]
    }
  ]
}

8.2 강제 규칙

UI는 SearchResponse를 그대로 렌더

UI에서 점수 계산/정렬 ❌

Metadata-Only 파일:

evidences = []

content_available = false

9. 저장소 구조 (Local File System)
9.1 기본 디렉토리
LocalFinderX/
├── data/
│   ├── manifest.json
│   ├── lancedb/          <-- LanceDB Data Folder
│   │   ├── ...
│   ├── bm25.bin
│   └── schema_version.json
├── logs/
│   └── indexing_errors.log
└── config/
    └── settings.json

9.2 저장 원칙

lancedb/: Vector + Text + Metadata (Files/Chunks 통합)

bm25.bin: lexical index (In-memory load)

manifest.json: fingerprint + 상태 관리

10. Manifest & 증분 인덱싱 규칙
10.1 Manifest 스키마
Manifest {
  "schema_version": "2.0",
  "files": {
    "/absolute/path": {
      "file_id": "uuid",
      "fingerprint": {...},
      "last_indexed_at": 1700002000.0
    }
  }
}

10.2 증분 인덱싱 로직 (강제)

파일 스캔

path 기준 manifest 조회

fingerprint 비교

변경 없음 → skip

변경 있음 → 기존 Chunk 삭제 → 재인덱싱

삭제된 파일 → FileRecord/Chunk 제거

11. Metadata-Only 파일 처리 규칙 (중요)

FileRecord는 생성

ChunkRecord는 생성 ❌

BM25 / Vector 검색에는 참여 ❌

File-level lexical match만 가능

최종 랭킹 시:

content indexed 파일 score × 1.0

metadata-only 파일 score × 0.4 감쇠

12. 예외 및 오류 처리
상황	처리
Chunk 생성 실패	해당 파일 전체 content_indexed=false
Embedding 실패	metadata-only로 downgrade
JSON 손상	해당 스토리지 무시 + 재인덱싱 요구
13. Phase 2 완료 기준 (DoD)

Phase 2는 아래가 모두 충족되어야 완료다.

모든 레코드 스키마가 문서로 고정됨

Storage 디렉토리 구조 확정

증분 인덱싱 로직이 문서로 명시됨

SearchResponse가 UI 바인딩 가능

Content vs Metadata-Only 통합 규칙 확정

14. 이후 변경 가능 범위
변경 가능

파일 저장 포맷(JSON → SQLite 등)

Embedding 차원 수

BM25 구현체

변경 불가

FileRecord / ChunkRecord 개념

Evidence 중심 UI 모델

Metadata-Only 정책