from typing import List, Dict, Optional
from indexer import FileIndexer
import os
from datetime import datetime

class SearchEngine:
    """
    Phase 3: 4. 메타데이터/최신성 기반 고급 랭킹 추가.
    
    중요 원칙: 검색 품질은 Free/Pro 동일.
    SearchEngine에 Free/Pro 구분 로직이 포함되지 않음.
    """
    
    def __init__(self, db_path: str = "./vector_db", model_name: str = "all-MiniLM-L6-v2", 
                 language: str = "en",
                 recency_boost: bool = True,
                 recency_days: int = 30,
                 source_boost: Optional[Dict[str, float]] = None):
        """
        Args:
            db_path: 벡터 DB 경로
            model_name: 임베딩 모델
            language: 언어 (en/kr)
            recency_boost: 최신 문서 가중치 활성화 (Free/Pro 동일)
            recency_days: 최신 문서로 간주할 일수
            source_boost: 소스별 가중치 (예: {"outlook": 1.2, "local": 1.0})
        """
        self.indexer = FileIndexer(db_path=db_path, model_name=model_name)
        self.language = language
        
        # Phase 3: 고급 랭킹 설정 (Free/Pro 동일하게 적용)
        self.recency_boost = recency_boost
        self.recency_days = recency_days
        self.source_boost = source_boost or {"local": 1.0, "outlook": 1.1, "onedrive": 1.0, "sharepoint": 1.0}

    def search_and_answer(self, query: str) -> Dict:
        """
        Performs RAG: Retrieve relevant docs -> Generate Answer.
        Returns a dictionary with 'answer' and 'files' (metadata).
        
        Phase 3: 메타데이터 기반 고급 랭킹 적용 (Free/Pro 동일)
        """
        print(f"Searching for: {query}")
        
        # 1. Retrieve relevant documents
        results = self.indexer.search(query, n_results=30)
        
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        
        if not documents:
            no_result_msg = "관련된 파일을 찾을 수 없습니다." if self.language == "kr" else "No relevant files found."
            return {
                "answer": no_result_msg,
                "files": []
            }

        # 2. Phase 3: Apply advanced ranking (recency + source boost)
        scored_results = []
        now = datetime.now()
        
        for i, doc in enumerate(documents):
            meta = metadatas[i]
            base_score = 1 - distances[i]  # 기본 유사도 점수
            
            # Recency boost
            recency_multiplier = 1.0
            if self.recency_boost:
                modified = meta.get('modified') or meta.get('created')
                if modified:
                    recency_multiplier = self._calculate_recency_boost(modified)
            
            # Source boost
            source = meta.get('type', 'local')
            source_multiplier = self.source_boost.get(source, 1.0)
            
            # Final score
            final_score = base_score * recency_multiplier * source_multiplier
            
            scored_results.append({
                'doc': doc,
                'meta': meta,
                'score': final_score,
                'original_distance': distances[i]
            })
        
        # Sort by final score (higher is better)
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        # 3. Construct Context and File List
        context = ""
        file_list = []
        seen_files = set()
        
        for result in scored_results:
            doc = result['doc']
            meta = result['meta']
            filename = meta.get('filename', 'Unknown')
            path = meta.get('source', '')
            score = result['score']
            
            if path not in seen_files:
                file_list.append({
                    "filename": filename,
                    "path": path,
                    "score": f"{score:.2f}",
                    "preview": doc[:100] + "...",
                    "metadata": meta
                })
                seen_files.add(path)
            
            file_label = "파일" if self.language == "kr" else "File"
            context += f"--- {file_label}: {filename} ---\n{doc}\n\n"

        # 4. Generate Answer (Offline Mode)
        answer = self._mock_llm_generation(query, context)
        
        return {
            "answer": answer,
            "files": file_list
        }

    def _calculate_recency_boost(self, modified_str) -> float:
        """
        Phase 3: 최신성 기반 가중치 계산.
        
        최근 recency_days 이내 문서에 부스트 적용.
        Free/Pro 동일하게 적용.
        """
        try:
            # ISO 형식 또는 timestamp 처리
            if isinstance(modified_str, (int, float)):
                modified = datetime.fromtimestamp(modified_str)
            elif isinstance(modified_str, str):
                # ISO 형식 파싱 시도
                modified_str = modified_str.replace('Z', '+00:00')
                if 'T' in modified_str:
                    modified = datetime.fromisoformat(modified_str.split('+')[0])
                else:
                    modified = datetime.fromisoformat(modified_str)
            else:
                return 1.0
            
            # 일수 차이 계산
            days_old = (datetime.now() - modified).days
            
            if days_old <= self.recency_days:
                # 최신일수록 높은 가중치 (최대 1.3x)
                boost = 1.0 + (0.3 * (1 - days_old / self.recency_days))
                return boost
            else:
                return 1.0
                
        except (ValueError, TypeError, AttributeError):
            return 1.0

    def _mock_llm_generation(self, query: str, context: str) -> str:
        """
        Fallback for offline mode: Returns the retrieved context directly.
        """
        file_count = len(context.split('--- 파일:')) - 1 if self.language == "kr" else len(context.split('--- File:')) - 1
        if file_count <= 0:
            file_count = len(context.split('---')) - 1

        if self.language == "kr":
            return f"""[검색 결과 요약]
질문과 가장 관련성 높은 {file_count}개의 파일을 찾았습니다.
왼쪽 목록에서 파일을 클릭하여 열거나, 내용을 확인하세요.

(상세 내용은 각 파일을 참고하세요)
"""
        else:
            return f"""[Search Results Summary]
Found {file_count} file(s) most relevant to your query.
Click on a file in the left panel to open it or view its contents.

(See each file for details)
"""

if __name__ == "__main__":
    engine = SearchEngine()
    print(engine.search_and_answer("매출 보고서 찾아줘"))
