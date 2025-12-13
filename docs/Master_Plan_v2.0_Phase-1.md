Local Finder X
Phase 1 — System Architecture & Module Boundary Definition

(v2.0 Greenfield Rebuild · Authoritative Document)

A. 문서 작성 강제 표준 (Document Constitution)

본 섹션은 이후 생성되는 모든 문서에 자동 적용되는 불변 규칙이다.

A.1 문서 계층 및 우선순위

모든 문서는 반드시 다음 계층 중 하나에 속해야 한다.

Strategy Level

Business Strategy

Product Strategy

Requirement Level

PRD

Design Level

Phase Documents (Phase 1, 2, …)

TDD (Technical Design Document)

UI Spec

Execution Level

Implementation Plan

Sprint Backlog

하위 문서는 상위 문서의 결정을 재해석하거나 수정할 수 없다.

A.2 문서 구성 강제 템플릿

모든 문서는 반드시 아래 구조를 포함한다.
(섹션이 “해당 없음”이어도 제목은 유지하고 명시적으로 기술)

문서 목적 및 적용 범위

본 문서가 고정하는 결정 사항 (Non-Negotiable Decisions)

In-Scope / Out-of-Scope

핵심 개념 정의 (Glossary / Definitions)

상세 설계 또는 정책 (본론)

인터페이스 / 경계 / 책임

예외, 실패, 에러 처리 원칙

완료 기준 (Definition of Done)

이 문서 이후 변경이 허용되는 범위

A.3 해석 금지 규칙

“의미상”, “보통은”, “일반적으로”라는 표현 사용 금지

“추후 논의”, “나중에 결정” 금지

모든 동작은 조건 → 처리 → 결과로 명시

1. 문서 목적 및 적용 범위
1.1 목적

본 문서는 Local Finder X v2.0의 시스템 아키텍처, 런타임 흐름, 모듈 경계, 의존성 방향을 완전히 고정한다.

이 문서 이후:

개발자는 폴더/파일/클래스 생성을 시작할 수 있어야 하며

이후 단계 문서(TDD, UI Spec)는 본 문서의 구조를 전제로만 작성된다.

1.2 적용 범위

v2.0 데스크톱 애플리케이션 전체

Free / Pro 공통 런타임

Indexing / Search / UI / Storage / Connectors 전부 포함

2. Phase 1에서 고정되는 결정 사항 (Non-Negotiable)

본 Phase에서 확정되며 이후 단계에서 변경 불가한 사항이다.

Layered Architecture 채택

UI → Core → Storage / Connectors 단방향 의존

Metadata-Only 파일도 Search Pipeline에 1급 시민으로 포함

Indexing과 Search는 완전히 분리된 파이프라인

UI는 Core의 결과를 “그대로 바인딩”한다 (UI 로직 금지)

3. In-Scope / Out-of-Scope (Phase 1 기준)
3.1 In-Scope

런타임 아키텍처 정의

모듈 경계 및 책임

스레딩/비동기 처리 원칙

데이터 흐름(인덱싱/검색)

3.2 Out-of-Scope

알고리즘 세부 파라미터(BM25 k값 등)

UI 위젯 상세

파일 파싱 로직 상세

성능 튜닝

4. 핵심 개념 정의 (Glossary)
용어	정의
FileRecord	모든 파일을 대표하는 단일 메타 단위
ChunkRecord	Content Indexed 파일의 검색 최소 단위
Metadata-Only File	내용 미분석, 메타데이터만 인덱싱된 파일
Evidence	검색 결과의 근거가 되는 Chunk
SearchResponse	UI에 전달되는 단일 검색 결과 모델
5. 전체 시스템 아키텍처 (Logical View)
5.1 레이어 구조 (강제)
┌────────────────────────────┐
│        UI Layer            │
│  (PyQt6, Panels, State)    │
└────────────▲───────────────┘
             │ (DTO only)
┌────────────┴───────────────┐
│        Core Layer          │
│  Search / Index / Domain   │
└────────────▲───────────────┘
             │
┌────────────┴───────────────┐
│  Storage & Connectors      │
│  LanceDB / BM25 / GraphAPI │
└────────────────────────────┘

의존성 규칙

UI는 Core만 참조

Core는 Storage / Connectors만 참조

Storage/Connectors는 상위 레이어를 절대 참조하지 않는다

6. 런타임 흐름 정의 (Runtime Flow)
6.1 인덱싱 파이프라인
[UI Indexing Page]
        │
        ▼
[IndexingController]
        │
        ▼
[FileEnumerator]
        │
        ├─ Content Indexed → [ContentExtractor] → [Chunker]
        │                                │
        │                                ▼
        │                        [Embedding / Tokenizer]
        │                                │
        └─ Metadata Only ────────────────┘
                                         ▼
                                 [LanceDB Writer]

핵심 원칙

파일 하나 실패해도 전체 중단 ❌

모든 파일은 FileRecord 생성 ⭕

ChunkRecord는 Content Indexed 파일만 생성

6.2 검색 파이프라인
[UI Search Panel]
        │
        ▼
[SearchController]
        │
        ▼
┌───────────── Hybrid Search ─────────────┐
│   Dense Retriever      BM25 Retriever   │
└─────────────▲──────────────▲────────────┘
              │              │
              └───── RRF Fusion ─────┐
                                     ▼
                            [File Aggregator]
                                     │
                                     ▼
                            [Evidence Builder]
                                     │
                                     ▼
                            [SearchResponse]
                                     │
                                     ▼
                                UI Binding

7. 모듈 경계 및 책임 (Authoritative)
7.1 UI Layer

역할

화면 렌더링

사용자 입력 수집

Core 호출

결과 바인딩

금지

검색 로직

점수 계산

데이터 가공

7.2 Core Layer
7.2.1 Indexing Domain

파일 분류(Content vs Metadata)

Chunk 생성

Token / Embedding 생성

Storage 호출

7.2.2 Search Domain

Query 처리

Retriever 실행

Fusion / Aggregation

Evidence 생성

SearchResponse 생성

7.3 Storage Layer

Vector Store (LanceDB)

BM25 Store

File Manifest

Persistence / Load

규칙

Core가 요구한 데이터만 반환

검색/정렬/의미 판단 ❌

7.4 Connectors

Local File System

Outlook (Graph API via Azure App)

OneDrive/SharePoint (Graph API or Sync Folder)

Google Drive (v2.0 UI only)

8. 스레딩 및 비동기 원칙
8.1 UI 스레드

렌더링

사용자 이벤트

상태 변경

8.2 Worker Thread

인덱싱 전체

검색 실행

파일 I/O

8.3 규칙

UI 스레드에서 파일 접근 ❌

Worker는 UI 객체 직접 접근 ❌

통신은 Signal/Callback 기반 DTO만 허용

9. 예외 및 실패 처리 원칙
상황	처리
파일 파싱 실패	스킵 + 오류 목록
인덱싱 중 앱 종료	재시작 시 재개
검색 중 오류	빈 결과 + 오류 메시지
Pro 기능 접근(Free)	UI 비활성 + 안내
10. Phase 1 완료 기준 (DoD)

Phase 1은 아래 조건을 모두 만족해야 완료로 간주한다.

모듈 폴더 구조가 생성 가능

의존성 방향이 문서로 고정

인덱싱/검색 런타임 흐름이 명확

이후 TDD가 본 문서를 그대로 참조 가능

“이 모듈은 어디에 속하는가?” 질문에 즉답 가능

11. 이후 단계에서 변경 가능한 범위

Phase 1 이후에도 변경 가능한 것

알고리즘 파라미터

모델 선택

UI 스타일

변경 불가

레이어 구조

데이터 흐름

Content vs Metadata 분리 정책

3-Panel UI 개념