# src/scheduler/runner.py
# Phase 3: 3.2. runner.py 예시에 따라 구현

import threading
import time
from typing import List, Tuple, Any, Optional, Callable
from datetime import datetime


class SchedulerRunner:
    """
    스케줄 실행기.
    
    스케줄러는 "언제/어디서 인덱싱을 실행할지"만 결정할 뿐,
    실제 인덱싱 로직은 기존 FileIndexer.index_connector()를 그대로 사용한다.
    따라서 검색 품질에 차이는 발생하지 않는다 (Free/Pro 모두 동일 인덱싱 파이프라인 사용).
    """
    
    def __init__(self, default_interval_seconds: int = 3600):
        """
        Args:
            default_interval_seconds: 기본 인덱싱 간격 (초, 기본 1시간)
        """
        self.default_interval_seconds = default_interval_seconds
        self._jobs: List[Tuple[Any, int, float]] = []  # (job, interval, last_run)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_job_complete: Optional[Callable] = None
        self._on_job_error: Optional[Callable] = None

    def add_job(self, job, interval_seconds: Optional[int] = None) -> None:
        """
        인덱싱 작업 추가.
        
        Args:
            job: IndexJob 프로토콜을 구현한 객체
            interval_seconds: 실행 간격 (None이면 기본값 사용)
        """
        interval = interval_seconds or self.default_interval_seconds
        # 즉시 실행되도록 last_run을 0으로 설정
        self._jobs.append((job, interval, 0.0))

    def remove_job(self, job_name: str) -> bool:
        """작업 제거."""
        original_count = len(self._jobs)
        self._jobs = [(j, i, l) for j, i, l in self._jobs if j.name != job_name]
        return len(self._jobs) < original_count

    def clear_jobs(self) -> None:
        """모든 작업 제거."""
        self._jobs.clear()

    def set_on_complete(self, callback: Callable) -> None:
        """작업 완료 콜백 설정."""
        self._on_job_complete = callback

    def set_on_error(self, callback: Callable) -> None:
        """작업 에러 콜백 설정."""
        self._on_job_error = callback

    def start(self) -> None:
        """스케줄러 시작 (백그라운드 스레드)."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """스케줄러 중지."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def is_running(self) -> bool:
        """스케줄러 실행 중인지 확인."""
        return self._running

    def run_now(self, job_name: str) -> Optional[dict]:
        """특정 작업 즉시 실행."""
        for i, (job, interval, last_run) in enumerate(self._jobs):
            if job.name == job_name:
                try:
                    result = job.run()
                    self._jobs[i] = (job, interval, time.time())
                    if self._on_job_complete:
                        self._on_job_complete(job.name, result)
                    return result
                except Exception as e:
                    if self._on_job_error:
                        self._on_job_error(job.name, e)
                    return {"error": str(e)}
        return None

    def _loop(self) -> None:
        """메인 스케줄러 루프."""
        while self._running:
            now = time.time()
            
            for i, (job, interval, last_run) in enumerate(self._jobs):
                if now - last_run >= interval:
                    try:
                        print(f"[Scheduler] Running job: {job.name}")
                        result = job.run()
                        self._jobs[i] = (job, interval, now)
                        
                        if self._on_job_complete:
                            self._on_job_complete(job.name, result)
                            
                    except Exception as e:
                        print(f"[Scheduler] Job error: {job.name} - {e}")
                        if self._on_job_error:
                            self._on_job_error(job.name, e)
            
            # 5초마다 체크
            time.sleep(5)

    def get_job_status(self) -> List[dict]:
        """등록된 작업들의 상태 조회."""
        now = time.time()
        return [
            {
                "name": job.name,
                "interval_seconds": interval,
                "last_run": datetime.fromtimestamp(last_run).isoformat() if last_run > 0 else None,
                "next_run_in_seconds": max(0, interval - (now - last_run)) if last_run > 0 else 0
            }
            for job, interval, last_run in self._jobs
        ]
