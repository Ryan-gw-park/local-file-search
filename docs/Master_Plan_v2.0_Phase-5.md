Local Finder X
Phase 5 — UI Specification & Interaction Design

(v2.0 Greenfield Rebuild · Authoritative Document)

0. 문서 목적 및 적용 범위
0.1 목적

본 문서는 Local Finder X v2.0의 모든 화면, 컴포넌트, 상태 전이, 이벤트 흐름을 고정한다.

이 문서는 다음 질문에 단일 답을 제공해야 한다.

“이 화면은 왜 존재하는가?”

“이 버튼을 누르면 정확히 무엇이 일어나는가?”

“이 상태에서 오류가 나면 UI는 어떻게 반응하는가?”

0.2 적용 범위

Global Sidebar

Search 화면(3-Panel)

Indexing 화면

About 화면

My Page 화면

공통 상태/로딩/에러 UX

1. Phase 5에서 고정되는 결정 사항 (Non-Negotiable)

Global Sidebar는 항상 표시

Search 화면에서만 3-Panel UI 사용

Center Panel은 “근거(Evidence)” 중심

UI는 SearchResponse DTO를 그대로 바인딩

Free/Pro 차별은 “비활성/안내”로만 표현, 기능 잠금 ❌

모든 비동기 작업은 명시적 로딩 상태를 가진다

2. In-Scope / Out-of-Scope
2.1 In-Scope

UI 레이아웃

컴포넌트 구조

상태(State)

이벤트(Event)

오류 UX

2.2 Out-of-Scope

시각 디자인 가이드(색상/폰트)

애니메이션

다국어 문구 번역 테이블

3. Global Sidebar (고정 UI)
3.1 목적

앱의 항상적 내비게이션 기준점

화면 전환 시 컨텍스트 손실 방지

3.2 구성 요소
아이콘	메뉴	설명
🔍	Search	검색 메인
📁	Indexing	검색 대상 관리
ℹ️	About	제품 정보
👤	My Page	라이선스/상태
3.3 동작 규칙

클릭 시 Main Content 교체

현재 선택 메뉴 강조

Search가 기본 진입 화면

4. Search 화면 — 3-Panel UI (핵심)
4.1 Right Panel — 대화형 검색 패널
목적

검색의 단일 입력점

검색 Refinement의 중심

구성 요소

상단 상태 바

모드 토글: FAST / SMART / ASSIST

검색 스코프 표시 (Free / Pro)

대화 히스토리 영역

입력 영역

텍스트 입력

검색 실행 버튼

필터 버튼

상태(State)
상태	설명
idle	대기
typing	입력 중
searching	검색 실행 중
error	검색 오류
이벤트(Event)
이벤트	처리
Enter / Search 클릭	SearchController 호출
필터 변경	다음 검색부터 적용
Evidence 선택	자동 질문 프리필
오류 UX

검색 실패:

“검색 중 오류가 발생했습니다”

이전 결과 유지

빈 결과:

“일치하는 파일을 찾지 못했습니다”

4.2 Left Panel — 검색 결과 파일 리스트
목적

파일 단위 검색 결과 개요

탐색/비교의 시작점

표시 항목(고정)

파일명(강조)

파일 타입 배지

Content Availability

Content Indexed

Metadata Only

경로(축약)

수정일

Score

Match Type

상태(State)
상태	설명
empty	검색 전
loading	검색 중
populated	결과 있음
error	오류
이벤트(Event)
이벤트	처리
단일 클릭	Center Panel 업데이트
더블 클릭	파일 열기
우클릭	컨텍스트 메뉴
Metadata-Only 파일 UX

Content badge: “Metadata Only”

Center Panel에 근거 대신 파일 정보 카드 표시

4.3 Center Panel — Evidence & Preview (정체성)
목적

“왜 이 파일이 결과인지” 설명

신뢰 형성의 핵심

구성

File Header

파일명 / 경로

파일 열기 버튼

Evidence Cards

Preview 영역(선택 Evidence)

Evidence Card 구성(고정)

요약 문장

점수 분해

스니펫(하이라이트)

위치 메타데이터

액션 버튼

Copy

Ask with this evidence

상태(State)
상태	설명
no_selection	파일 미선택
loading	전환 중
populated	Evidence 표시
metadata_only	근거 없음 안내
오류 UX

Evidence 생성 실패:

“근거를 표시할 수 없습니다”

파일 정보만 유지

5. Indexing 화면 (📁 Indexing)
목적

검색 대상 통제 센터

Free/Pro 스코프 자연스러운 노출

구성 영역

파일 타입 필터

외부 소스 연동

Outlook

OneDrive / SharePoint

Google Drive (UI only)

폴더 트리 선택

인덱싱 실행/상태

결과 요약

상태(State)
상태	설명
idle	대기
indexing	실행 중
completed	완료
error	실패
이벤트(Event)
이벤트	처리
인덱싱 실행	IndexingController 호출
중단	안전 종료
재인덱싱	manifest 초기화 후 실행
오류 UX

개별 파일 실패:

오류 목록 표시

전체 중단 ❌

6. About 화면 (ℹ️ About)
요구사항

기존 About 내용 그대로

수정 ❌

스크롤 가능한 정적 페이지

7. My Page 화면 (👤 My Page)
구성

라이선스 상태

Pro 활성화 입력

검색 스코프 요약

앱 정보

상태(State)
상태	설명
free	Free
pro	Pro
invalid	라이선스 오류
UX 규칙

Pro 기능은 비활성 + 안내

“왜 Pro가 필요한지” 설명 텍스트 필수

8. 공통 로딩 / 에러 UX
로딩

스켈레톤 or Spinner

작업 취소 가능 여부 명시

에러

기술적 메시지 ❌

사용자 이해 가능한 문구 ⭕

9. Phase 5 완료 기준 (DoD)

Phase 5는 아래가 모두 충족되어야 완료다.

모든 화면이 명세됨

모든 버튼/입력의 동작 정의

상태/이벤트/오류 처리 명확

UI에서 Core 로직 추정 필요 없음

PyQt6로 바로 구현 가능

10. 이후 변경 가능 범위
변경 가능

레이아웃 비율

문구

아이콘 스타일

변경 불가

3-Panel 구조

Evidence 중심 UX

Global Sidebar 구조