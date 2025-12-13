Local Finder X
Phase 4 — Search Pipeline & Hybrid Retrieval Design

(v2.0 Greenfield Rebuild · Authoritative Document)

0. 문서 목적 및 적용 범위
0.1 목적

본 문서는 Local Finder X v2.0의 검색(Search) 동작을 완전히 고정한다.

이 문서가 답해야 하는 질문:

“이 쿼리가 어떤 단계들을 거쳐 결과가 되었는가?”

“왜 이 파일이 위에 나오고, 저 파일은 아래인가?”

“왜 이 근거 스니펫이 선택되었는가?”

0.2 적용 범위

Query Processing

Dense Retrieval

Lexical(BM25) Retrieval

RRF Fusion

File-level Aggregation

Evidence(근거) 생성

FAST / SMART / ASSIST 모드 정의

1. Phase 4에서 고정되는 결정 사항 (Non-Negotiable)

검색은 항상 Hybrid Search를 기본값으로 사용

Dense / Lexical 검색은 완전히 독립 실행

검색 품질의 판단은 File 단위, Chunk는 근거일 뿐

Metadata-Only 파일도 검색 결과에 포함

UI는 SearchResponse를 그대로 렌더링

LLM은 검색 순위 결정에 관여하지 않음

2. In-Scope / Out-of-Scope
2.1 In-Scope

검색 알고리즘 파이프라인

점수 결합 규칙

모드별 파이프라인 옵션

Evidence 생성 규칙

2.2 Out-of-Scope

UI 위젯 구현

인덱싱 로직

클라우드/외부 검색

3. 검색 파이프라인 전체 흐름 (Authoritative)
[User Query]
     │
     ▼
[Query Processor]
     │
     ├─ Dense Query Vector
     │
     ├─ Lexical Query Tokens
     │
     ▼
┌──────────── Dense Retriever ────────────┐
│  Chunk-level similarity search          │
└────────────▲───────────────────────────┘
             │
┌────────────┴────────────┐
│  BM25 Retriever         │
│  (Chunk + File tokens)  │
└────────────▲────────────┘
             │
        [RRF Fusion]
             │
        [File Aggregator]
             │
        [Evidence Selector]
             │
        [SearchResponse Builder]
             │
             ▼
              UI

4. Query Processing
4.1 Query Input 규칙

입력은 자연어 원문 그대로 유지

길이 제한:

최대 512자

초과 시 뒤에서 truncate

빈 문자열 / 공백만 입력:

검색 실행 ❌

UI 경고

4.2 Query 변환 결과물
목적	생성물
Dense 검색	query_embedding
Lexical 검색	query_tokens
Query Tokens 규칙

한국어:

Kiwi 사용

NNG, NNP, SL, SN

영문:

lowercase

length ≥ 2

5. Dense Retriever (Semantic Search)
5.1 검색 대상

ChunkRecord.embedding

Content Indexed 파일만 대상

Metadata-Only 파일은 Dense 검색 ❌

5.2 검색 방식

Similarity: cosine similarity

Top-N: 기본 50

반환값:

DenseResult {
  "chunk_id": "uuid",
  "file_id": "uuid",
  "score": 0.0 ~ 1.0
}

5.3 Dense Retriever 실패 처리

결과 0개:

Lexical 검색 결과만 사용

모델 오류:

전체 Dense 결과 무시

오류 로그 기록

6. Lexical Retriever (BM25)
6.1 검색 대상

Content Indexed 파일:

Chunk tokens

Metadata-Only 파일:

File-level tokens

filename

path

author

6.2 반환 구조
LexicalResult {
  "doc_id": "chunk_id | file_id",
  "file_id": "uuid",
  "score": float
}

6.3 Lexical 검색 규칙

Top-N: 기본 50

Chunk-level 결과는 file_id로 매핑 가능해야 함

결과 0개 허용

7. RRF Fusion (Rank-based Combination)
7.1 RRF 적용 대상

Dense 결과 랭킹

Lexical 결과 랭킹

7.2 RRF 수식 (강제)
RRF_score(file) =
  Σ ( 1 / (k + rank_dense) ) +
  Σ ( 1 / (k + rank_lexical) )


k = 60 (고정)

rank는 1부터 시작

Dense / Lexical 중 하나만 존재해도 계산

7.3 RRF 적용 단위

Chunk 단위 ❌

File 단위 ⭕

Chunk 결과는 file_id 기준으로 묶어
“이 파일이 몇 위였는지”로만 사용한다.

8. File Aggregation (중요)
8.1 목적

Chunk 중심 검색 결과를 File 중심 결과로 변환

8.2 File Score 계산 규칙 (강제)
file_score =
  max(chunk_rrf_scores) +
  α × mean(top_3_chunk_rrf_scores)


α = 0.2 (고정)

chunk_rrf_scores:

해당 file에 속한 chunk들의 RRF 점수

8.3 Metadata-Only 파일 점수 처리
final_file_score = file_score × 0.4


0.4는 Phase 2에서 고정된 감쇠 계수

감쇠는 aggregation 이후 적용

9. Evidence 생성 규칙 (Explainable Core)
9.1 Evidence 선택 규칙

File당 최대 5개

선택 기준:

chunk_rrf_score 상위

서로 다른 위치 메타데이터 우선

9.2 Evidence 구성 요소 (재확인)

summary (템플릿 기반)

snippet (200~500 chars)

highlight:

query tokens

location metadata

9.3 Metadata-Only 파일 Evidence

Evidence 생성 ❌

UI에는:

“이 파일은 메타데이터만 인덱싱되었습니다” 메시지 표시

10. SearchResponse 생성
10.1 결과 제한

File 결과 최대 50개

UI 기본 노출: 상위 20개

10.2 SearchResponse 필드 (재확인)

query

elapsed_ms

results[]

각 result:

file (FileRecord)

score

match_type:

semantic / lexical / hybrid

content_available

evidences[]

11. FAST / SMART / ASSIST 모드 정의
11.1 공통 원칙

기능 차이 없음

파이프라인 옵션만 변경

11.2 모드별 차이
항목	FAST	SMART	ASSIST
Dense Top-N	20	50	50
BM25 Top-N	20	50	50
Evidence 수	2	3	5
Reranker	❌	❌	⭕ (옵션)
Latency 목표	최저	균형	정확도
12. 오류 및 예외 처리
상황	처리
Dense 실패	Lexical만 사용
Lexical 실패	Dense만 사용
둘 다 실패	빈 결과
Aggregation 오류	해당 파일 제외
전체 오류	빈 SearchResponse + 메시지
13. Phase 4 완료 기준 (DoD)

Phase 4는 아래가 모두 충족되어야 완료다.

Hybrid Search 전체 흐름이 문서로 고정됨

File-level 점수 계산 규칙 명확

Evidence 생성 규칙 명시

Metadata-Only 파일의 검색 참여 방식 확정

모드별 파이프라인 차이 고정

14. 이후 변경 가능 범위
변경 가능

Top-N 수치

α 계수

RRF k 값

Evidence 개수

변경 불가

Hybrid Search 구조

File 중심 랭킹

Explainable Evidence 모델