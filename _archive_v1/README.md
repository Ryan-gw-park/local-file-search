# Local AI File Search

**100% 오프라인으로 작동하는 AI 기반 로컬 파일 검색기**

비개발자도 쉽게 설치하고 사용할 수 있는 Windows/Mac용 오피스 문서 검색 도구입니다.

---

## 주요 기능

- **시맨틱 검색**: 키워드가 아닌 의미 기반 검색 (예: "돈" 검색 시 "예산", "비용", "매출" 문서도 찾음)
- **100% 오프라인**: 인터넷 연결 없이 완전히 로컬에서 작동
- **다국어 지원**: 한국어/영어 UI 및 검색 지원
- **읽기 전용**: 파일을 수정하거나 삭제하지 않음

---

## 지원 파일 형식

| 확장자 | 설명 |
|--------|------|
| `.docx` | Microsoft Word |
| `.xlsx` | Microsoft Excel |
| `.pptx` | Microsoft PowerPoint |
| `.txt` | 텍스트 파일 |
| `.md` | 마크다운 파일 |
| `.pdf` | PDF 문서 |

---

## 아키텍처

```
+-------------------------------------------------------------------+
|                        User Interface (PyQt6)                     |
|  +-----------------------------+--------------------------------+ |
|  |      File Table (60%)       |     Chat Sidebar (40%)         | |
|  |  - Filename                 |  - AI Response                 | |
|  |  - Path                     |  - Search Input                | |
|  |  - Relevance Score          |  - Search Button               | |
|  |  - Preview                  |                                | |
|  +-----------------------------+--------------------------------+ |
+-------------------------------------------------------------------+
                                |
                                v
+-------------------------------------------------------------------+
|                     SearchEngine (RAG Pattern)                    |
|  1. Query -> Embedding -> Vector Search                           |
|  2. Top-K 관련 문서 청크 검색                                     |
|  3. 결과 집계 및 응답 생성                                        |
+-------------------------------------------------------------------+
                                |
                                v
+-------------------------------------------------------------------+
|                       FileIndexer                                 |
|  +-------------+    +-------------+    +---------------------+    |
|  | Text Extract| -> | Text Chunk  | -> | Sentence Transformer|    |
|  | (docx/pdf/  |    | (1000 char  |    | Embedding Generation|    |
|  |  xlsx/txt)  |    |  + overlap) |    |                     |    |
|  +-------------+    +-------------+    +---------------------+    |
+-------------------------------------------------------------------+
                                |
                                v
+-------------------------------------------------------------------+
|           SimpleVectorStore (Lightweight Vector DB)               |
|  - NumPy & Pickle 기반 로컬 저장 (Zero-Dependency)                |
|  - 벡터 유사도 검색 (Cosine Similarity)                           |
|  - 메타데이터: 파일명, 경로, 생성일, 청크 인덱스                  |
+-------------------------------------------------------------------+
```

---

## 프로젝트 구조

```
file_searcher/
├── src/
│   ├── __init__.py
│   ├── main.py              # 기본 진입점
│   ├── main_en.py           # 영어 버전 진입점
│   ├── main_kr.py           # 한국어 버전 진입점
│   ├── ui.py                # PyQt6 GUI 구현
│   ├── indexer.py           # 파일 인덱싱 및 텍스트 추출
│   └── search_engine.py     # 검색 및 RAG 구현
├── build.bat                # Windows 원클릭 빌드 스크립트
├── build.spec               # PyInstaller 기본 설정
├── build_en.spec            # 영어 버전 빌드 설정
├── build_kr.spec            # 한국어 버전 빌드 설정
├── requirements.txt         # Python 의존성
├── FAQ.md                   # 자주 묻는 질문 (한국어)
├── walkthrough.md           # 사용자 가이드 (영어)
└── packaging_guide.md       # 빌드/설치 가이드 (한국어)
```

---

## 핵심 컴포넌트

### 1. FileIndexer (src/indexer.py)

파일 텍스트 추출 및 벡터 임베딩 생성을 담당합니다.

**주요 기능:**
- 오피스 문서 및 PDF에서 텍스트 추출 (python-docx, PyPDF2, openpyxl 등)
- 텍스트 청킹 (1000자 단위, 100자 오버랩)
- Sentence Transformer를 이용한 벡터 임베딩 생성
- SimpleVectorStore에 벡터 및 메타데이터 저장

```python
class FileIndexer:
    def extract_text(file_path: str) -> str  # 텍스트 추출
    def index_directory(directory_path: str) -> Dict  # 폴더 전체 인덱싱
    def index_file(file_path: str)  # 단일 파일 인덱싱
    def search(query: str, n_results: int) -> results  # 벡터 검색
```

### 2. SearchEngine (src/search_engine.py)

RAG(Retrieval-Augmented Generation) 패턴을 구현합니다.

**주요 기능:**
- 쿼리 임베딩 및 유사 문서 검색
- 검색 결과 집계 및 중복 제거
- 다국어 응답 메시지 생성

```python
class SearchEngine:
    def search_and_answer(query: str) -> Dict  # 검색 및 응답 생성
    def _mock_llm_generation(query, context) -> str  # 오프라인 응답 생성
```

### 3. ChatWindow (src/ui.py)

PyQt6 기반의 데스크톱 GUI를 제공합니다.

**주요 기능:**
- 파일 탐색기 스타일의 테이블 뷰
- 실시간 검색 및 결과 표시
- 백그라운드 인덱싱 (QThread)
- 파일 더블클릭으로 기본 앱에서 열기

---

## 기술 스택

| 카테고리 | 기술 |
|----------|------|
| **언어** | Python 3.9+ |
| **GUI** | PyQt6 |
| **벡터 DB** | SimpleVectorStore (NumPy + Pickle) |
| **임베딩** | Sentence Transformers |
| **NLP** | LangChain (텍스트 분할) |
| **문서 파싱** | python-docx, PyPDF2, openpyxl |
| **패키징** | PyInstaller |

---

## AI 모델

### 영어 버전
- **모델**: `all-MiniLM-L6-v2`
- **크기**: ~80MB
- **특징**: 빠른 속도, 영어 최적화

### 한국어 버전
- **모델**: `paraphrase-multilingual-MiniLM-L12-v2`
- **크기**: ~400MB
- **특징**: 50+ 언어 지원, 한국어 포함

두 모델 모두 사전 학습된 상태로 배포되며, 사용자 데이터를 추가 학습하지 않습니다.

---

## 데이터 흐름

```
1. 사용자가 폴더 선택
        |
        v
2. IndexingThread 시작 (백그라운드)
        |
        v
3. 각 파일에 대해:
   - 텍스트 추출
   - 1000자 청크로 분할
   - 벡터 임베딩 생성
   - SimpleVectorStore에 저장
        |
        v
4. 인덱싱 완료 (UI에 결과 표시)
        |
        v
5. 사용자가 검색 쿼리 입력
        |
        v
6. 쿼리 임베딩 -> Vector Search (Cosine Similarity)
        |
        v
7. Top-5 관련 청크 반환
        |
        v
8. UI에 결과 표시 (테이블 + 채팅)
```

---

## 보안 및 개인정보 보호

- **100% 오프라인**: 외부 서버와 통신 없음
- **화이트리스트 방식**: 지정된 문서 확장자만 읽음
- **읽기 전용**: 파일 수정/삭제 없음
- **사전 학습 모델**: 사용자 데이터 학습 없음
- **임시 파일 무시**: `~$` 접두사 파일 스킵

자세한 내용은 FAQ.md를 참조하세요.

---

## 빌드 및 설치

### 개발 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 실행 (한국어)
python src/main_kr.py

# 실행 (영어)
python src/main_en.py
```

### 실행 파일 빌드 (Windows)

```bash
# build.bat 실행 후 언어 선택
build.bat
```

자세한 빌드 가이드는 packaging_guide.md를 참조하세요.

---

## 라이선스

MIT License

---

## 연락처

버그 리포트 및 제안: backnine.works@gmail.com
