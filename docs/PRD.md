# Local Finder X PRD (Product Requirements Document)

**v2.0 Explainable Hybrid Local Search Platform**
*(Greenfield Rebuild · Final Source of Truth)*

---

## 0. 문서 목적과 적용 범위
### 0.1 목적
본 PRD는 Local Finder X v2.0을 처음부터 새로 개발하기 위한 최상위 제품 요구사항 문서입니다.
개발팀이 “추정”, “생략”, “임의 해석” 없이 구현할 수 있도록 상세 기준을 규정합니다.

### 0.2 개발 원칙 (Non-Negotiable)
*   **Local-First**: 런타임 중 외부 네트워크 통신 없음.
*   **Explainable Search**: 모든 검색 결과는 “왜 나왔는지” 설명 가능해야 함.
*   **기능 차별 없는 무료 요금제**: Free/Pro는 검색 성능·기능 동일. 차별은 스코프(Scope)만.
*   **기존 사무환경 존중**: MS Office, Outlook, 로컬 파일 중심.

---

## 1. 검색 대상 및 인덱싱 정책 (Revised)

### 1.1 콘텐츠 인덱싱 대상 (Content Indexing)
파일 내용을 추출, 청킹, 임베딩하여 **의미 및 키워드 검색**을 지원합니다.

*   **Office**: .docx, .xlsx, .pptx
*   **Document**: .pdf, .md
*   **Outlook (Pro)**: 이메일 본문, 제목, 첨부파일(지원 포맷만)

### 1.2 메타데이터 전용 인덱싱 대상 (Metadata-Only Indexing) **[NEW]**
파일 내용은 분석하지 않지만, **파일명, 경로, 작성자, 수정일** 등 메타데이터만 인덱싱하여 검색 결과에 노출합니다.

*   **대상**: 지원 콘텐츠 포맷 외 모든 파일 (.zip, .psd, .hwp, .csv 등)
*   **목적**: "내용은 몰라도 파일이 있었던 것 같은데"라는 니즈 해결.
*   **UI 표현**: 검색 결과에서 "Metadata Only" 배지 표시, 미리보기(Center Panel)에서는 파일 정보만 표시.

---

## 2. 전역 UI 구조 (Global Navigation) **[NEW]**

### 2.1 UI 레이아웃
왼쪽에 고정된 **Global Sidebar**를 도입하여 기능을 명확히 분리합니다.

*   **검색 (Search)**: 메인 검색 화면 (3-Panel)
*   **인덱싱 (Indexing)**: 검색 대상 관리 및 실행
*   **정보 (About)**: 앱 정보 (기존 유지)
*   **마이 페이지 (My Page)**: 라이선스 관리 및 통계

---

## 3. Search 화면 (🔍 Search)
3-Panel UI를 유지하며, 메타데이터 검색 결과를 수용하도록 확장합니다.

### 3.1 Left Panel: Result List
*   **표시**: 파일명, 배지(타입), 경로, 점수, **Content Availability Badge**
    *   `Content Indexed`: 내용 검색 가능
    *   `Metadata Only`: 파일명/경로만 매칭됨
*   **동작**:
    *   Content Indexed 클릭 → Center Panel에 Evidence Cards 표시
    *   Metadata Only 클릭 → Center Panel에 **"메타데이터만 인덱싱됨"** 안내 및 파일 정보 카드 표시

### 3.2 Center Panel: Explainability Core
*   **Content Indexed**: 근거(Snippet), 위치(Page/Slide), 이유 설명 표시
*   **Metadata Only**: 파일 열기 버튼, 경로 복사, 메타데이터 상세(크기, 수정일 등)만 표시

### 3.3 Right Panel: Assistant
*   대화형 검색 및 필터 조작 (FAST/SMART/ASSIST 모드)

---

## 4. Indexing 화면 (📁 Indexing) **[NEW]**
사용자가 검색 대상을 명확히 제어하고 결과를 투명하게 확인하는 대시보드입니다.

### 4.1 구성 요소
1.  **파일 타입 필터**:
    *   Office / PDF / MD 체크박스 (기본 선택)
    *   Outlook Email (Pro 전용)
    *   **"기타 파일(메타데이터만)"** 체크박스
2.  **외부 소스 연동**:
    *   **Outlook**: "연동하기" 버튼 (Pro 안내)
    *   **OneDrive / SharePoint**: "동기화된 폴더 추가" (API 방식 아님, 로컬 폴더 선택)
3.  **폴더 트리 (Scope Select)**:
    *   로컬 드라이브 트리 뷰 (체크박스 다중 선택)
    *   선택된 폴더의 "총 파일 수 / 콘텐츠 대상 수" 실시간 표시 요망
4.  **실행 및 상태**:
    *   "인덱싱 실행" 버튼
    *   진행률: 전체/완료/실패 파일 수
    *   결과 요약: **"총 00개 (콘텐츠 00, 메타데이터 00)"** 구분 표시

---

## 5. 데이터 모델 및 기술 요구사항

### 5.1 통합 검색 로직
*   **FileRecord**: 모든 파일 공통 (content_indexed: bool 필드 추가)
*   **ChunkRecord**: 콘텐츠 인덱싱 파일만 보유
*   **랭킹**: 콘텐츠 매칭 점수 우선, 메타데이터 매칭 점수는 패널티(Decay) 적용하여 통합 정렬.

### 5.2 Storage (LanceDB)
*   **스키마**:
    *   `vector` (1024)
    *   `text` (Snippet)
    *   `metadata` (JSON)
    *   `content_indexed` (Boolean) - 필터링용
    *   `is_metadata_only` (Boolean) - 구분용

---

## 6. 최종 DoD (v2.0 완성 기준)
*   콘텐츠 인덱싱 + 메타데이터 전용 인덱싱 동시 지원
*   Global Sidebar 및 Indexing 대시보드 구현
*   메타데이터 전용 파일도 검색 결과에 노출 (미리보기 없음 처리)
*   Free/Pro 스코프 차이가 Indexing 화면에 명확히 반영
*   런타임 외부 통신 없음
