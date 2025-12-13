# 🔍 Local Finder X

**100% 오프라인 AI 파일 검색 엔진**

Windows/Mac용 MS Office 문서 검색 도구. 시맨틱 AI 검색으로 파일명이 아닌 **내용**으로 파일을 찾습니다.

## ⭐ 주요 특징

- **시맨틱 검색** - "예산" 검색 시 "비용", "매출" 문서도 찾음
- **100% 오프라인** - 파일 정보가 외부로 전송되지 않음
- **하이브리드 검색** - Dense + BM25 + RRF Fusion
- **다국어 지원** - 한국어 + 영어

## 📁 지원 파일 형식

| 확장자 | 설명 |
|--------|------|
| `.docx` | Microsoft Word |
| `.xlsx` | Microsoft Excel |
| `.pptx` | Microsoft PowerPoint |
| `.pdf` | PDF 문서 |
| `.md` | 마크다운 |

## 🚀 설치 및 실행

```bash
# 1. Clone
git clone https://github.com/Ryan-gw-park/local-finder-x.git
cd local-finder-x

# 2. 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 의존성 설치
pip install -e .

# 4. 실행
python -m src.app.main
```

## 🧠 AI 모델

| 모드 | 모델 | 크기 | 권장 RAM |
|------|------|------|----------|
| 빠른 모드 | all-MiniLM-L6-v2 | ~80MB | 4GB |
| 균형 모드 | paraphrase-multilingual-MiniLM-L12-v2 | ~400MB | 8GB |
| 정밀 모드 | BAAI/bge-m3 | ~2.3GB | 16GB+ |

첫 실행 시 Setup Wizard에서 모델을 선택합니다.

## 🔐 보안 및 프라이버시

- **100% 오프라인 작동** - 외부 서버 통신 없음
- **로컬 저장소만 사용** - 임베딩/인덱스 모두 로컬
- **읽기 전용** - 파일 수정/삭제 없음
- **추론 전용 모델** - 사용자 데이터 학습 없음

## 📦 Free vs Pro

| 기능 | Free | Pro |
|------|:----:|:---:|
| 로컬 파일 검색 | ✅ | ✅ |
| 검색 품질 | 동일 | 동일 |
| Outlook 이메일 | ❌ | ✅ |
| OneDrive 연동 | ❌ | ✅ |

## 📞 연락처

Email: backnine.works@gmail.com

## 📄 라이선스

MIT License

---

© 2025 Local Finder X. All rights reserved.
