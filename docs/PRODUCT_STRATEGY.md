# Local Finder X 제품 전략 (Product Strategy)

**"Explainable Context Engine for Local Knowledge Workers"**

## 1. 제품 전략의 목적 (Object)
이 문서는 다음 질문에 답하기 위해 존재합니다.
*   우리는 어떤 문제를 어떤 순서로 해결하는가?
*   어떤 기능이 핵심이고, **무엇을 하지 않는가?**
*   Free ↔ Pro의 차별을 UX와 제품 구조로 어떻게 자연스럽게 만드는가?
*   “무엇을 왜 만들고, 무엇을 안 만들지”를 결정하는 기준점입니다.

---

## 2. 제품 전략의 핵심 명제 (Product Thesis)

> **Local Finder X는 ‘문서를 더 많이 찾게 해주는 도구’가 아니라, ‘문서를 찾는 이유와 맥락을 즉시 이해하게 해주는 도구’다.**

따라서 제품 전략의 중심은 다음과 같이 이동합니다:
*   검색 정확도 자체 ❌ → **Explainability (설명 가능성)**
*   UI 화려함 ❌ → **Context (맥락의 시각화)**
*   LLM 과시 ❌ → **Local-First Trust (신뢰)**

---

## 3. 제품 성공의 핵심 지표 (North Star Metrics)

### Primary Metrics
1.  **Search-to-Open Time**: 검색어 입력부터 원하는 파일을 열기까지 걸리는 시간 (가장 중요)
2.  **Evidence Interaction Rate**: 검색 결과 패널의 “근거 스니펫”을 클릭/확인한 비율
3.  **Search Success Rate**: 오타 수정이나 재검색 없이 한 번에 원하는 파일을 찾은 비율

### Secondary Metrics
*   Pro 전환율
*   Pro 사용자의 검색 대상(이메일/클라우드) 활용 비율
*   검색 쿼리당 파일 오픈 시도 횟수 감소 (정확하게 찾았다는 증거)

---

## 4. 핵심 사용자 시나리오 (Core Use Cases)

### UC-1. “기억은 안 나지만 분명히 있었던 파일”
*   **입력**: “작년 4분기 예산 조정 관련 자료”
*   **기대**: 파일 리스트 + **“이 파일의 p.12에서 예산 조정 관련 문장”** 하이라이트 + [바로 열기]

### UC-2. “버전이 너무 많은 문서”
*   **입력**: “그때 고객 피드백 반영한 최종안”
*   **기대**: 수많은 `v1`, `final` 중 **가장 관련 높은 버전** 상단 노출 + (Pro) 관련 이메일 연결

### UC-3. “이메일에서 시작된 업무” (Pro)
*   **입력**: “대표님이 보낸 메일에 첨부된 보고서”
*   **기대**: 이메일 본문과 첨부된 문서 내용을 통합 검색하여, **해당 파일이 어떤 메일 맥락에서 왔는지** 확인

---

## 5. 제품 전략 4대 축 (Product Pillars)

### Pillar 1. Explainable Search First
*   **전략**: 검색 결과는 항상 근거(Evidence)를 동반해야 합니다. 파일명만 나열하는 UI는 폐기합니다.
*   **구현 원칙**:
    *   Result = File Meta + **Top-N Evidence Chunks**
    *   Evidence는 텍스트 스니펫, 페이지/슬라이드 정보, "왜 관련 있는지"에 대한 한 줄 설명을 포함합니다.
*   **하지 않는 것**: 전체 문서 AI 요약 기본 제공 ❌, LLM 기반의 근거 없는 추측 답변 ❌

### Pillar 2. Hybrid Retrieval, LLM-Optional
*   **전략**: 검색 품질의 80%는 Retrieval(탐색)에서 해결하고, LLM은 "설명/보조" 역할만 담당합니다.
*   **구현 원칙**: Dense(의미) + BM25(키워드) 독립 실행 후 RRF 결합. 구조 기반 청킹으로 의미 보존.
*   **하지 않는 것**: "LLM이 알아서 답을 만들어준다"는 경험 ❌, 클라우드 LLM 필수 의존 ❌

### Pillar 3. Local-First Trust, Zero Surprise
*   **전략**: 사용자는 “이 앱이 내 데이터를 어떻게 다루는지” 항상 이해하고 통제해야 합니다.
*   **구현 원칙**: 모든 데이터는 로컬에만 존재. 네트워크 접근은 명시적 허용 전까지 차단.
*   **하지 않는 것**: 백그라운드 몰래 업로드 ❌, 모호한 "AI 처리 중" 메시지 ❌

### Pillar 4. Free는 넓게, Pro는 깊게
*   **전략**: 성능/알고리즘 차별 ❌. **검색 대상의 범위와 연결성**으로 차별화.
*   **Free**: 로컬 MS Office 문서 검색 영구 무료. 모든 기능 동일.
*   **Pro**: Outlook, OneDrive, SharePoint 연결. **이메일 ↔ 문서 ↔ 버전 간 컨텍스트 그래프** 제공.
*   **UX**: 기능을 막아놓는 자물쇠 ❌, "이메일까지 연결하면 더 잘 보인다"는 확장 제안 ⭕

---

## 6. 제품 구조 전략 (Information Architecture)

### 6.1 3-Panel UI (Fixed Strategy)
*   **Left**: 검색 결과 리스트 (파일 중심)
*   **Center**: **근거 & 맥락 설명 (제품의 정체성)**
*   **Right**: 대화형 검색 & 상세 Refinement

### 6.2 데이터 모델 전략
*   사용자 멘탈 모델: "파일 + 근거"
*   Pro 확장 모델: "이메일 ↔ 파일 ↔ 버전" 연결 그래프

---

## 7. 기술 구현 전략과 제품 전략의 연결
*   **원칙**: UI 구조와 데이터 모델 선행 → Hybrid Search로 리콜 확보 → 구조 청킹으로 근거 품질 향상.
*   **DB 전략**: **서버리스/임베디드 아키텍처 준수**. 별도 설치가 필요한 무거운 DB(Milvus/Weaviate 등) 대신, 파일 기반의 **LanceDB**를 사용하여 로컬 환경 최적화.

---

## 8. 로드맵 개요 (Product View)

### Phase 1 — Explainable Local Search (v2.0)
*   3패널 UI 완성
*   Hybrid Search (BM25+Dense)
*   Evidence Cards (근거 시각화)

### Phase 2 — Context Expansion (v2.x)
*   Outlook 이메일 인덱싱 (Pro Feature)
*   이메일 ↔ 첨부파일 연결 UX

### Phase 3 — Long-Term Context (v3)
*   문서 버전 관계 추론
*   업무 흐름 타임라인 뷰

---

## 9. Definition
> **"Local Finder X의 제품 전략은 ‘검색을 더 똑똑하게 만드는 것’이 아니라, ‘검색 결과를 믿을 수 있게 만드는 것’이다."**
