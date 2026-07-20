"""검증 데이터를 CSV·Parquet 로 저장하고 읽기/쓰기 시간 측정·비교.

작성자 : 신주용 (광주 3반)

변경 이력
- 2026-07-20 최초 작성
"""

import time
from pathlib import Path

import pandas as pd


def _best_ms(fn, repeat: int = 5) -> float:
    """fn 을 여러 번 실행해 최소 시간(ms) 반환.

    첫 1회는 워밍업으로 버린다 - pyarrow 등 엔진 초기화 비용이 측정에 섞이면
    (첫 parquet 호출이 수백 ms) 형식 간 비교가 왜곡되기 때문.
    입력 : fn - 인자 없는 콜러블, repeat - 측정 반복 횟수
    반환 : 최소 실행 시간(ms) - 노이즈를 줄인 대표값
    """
    fn()  # 워밍업 (import/엔진 초기화 비용 제외)
    best = float("inf")
    for _ in range(repeat):
        start = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - start)
    return round(best * 1000, 3)


def save_and_benchmark(records: list[dict], out_dir: Path) -> dict:
    """레코드를 CSV·Parquet 로 저장하고 형식별 쓰기/읽기 시간을 측정.

    입력 : records - 검증 통과 레코드 리스트, out_dir - 저장 폴더
    반환 : {"csv": {...}, "parquet": {...}} 형식별 쓰기(ms)·읽기(ms)·크기(B)
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records)
    csv_path = out_dir / "weather.csv"
    pq_path = out_dir / "weather.parquet"

    # 형식별 (쓰기, 읽기) 동작을 정의해 동일 방식으로 시간 측정
    jobs = [
        ("csv", csv_path,
         lambda: df.to_csv(csv_path, index=False),
         lambda: pd.read_csv(csv_path)),
        ("parquet", pq_path,
         lambda: df.to_parquet(pq_path, index=False),
         lambda: pd.read_parquet(pq_path)),
    ]

    result = {}
    for fmt, path, write, read in jobs:
        result[fmt] = {
            "write_ms": _best_ms(write),
            "read_ms": _best_ms(read),
            "size_bytes": path.stat().st_size,
        }
    return result
