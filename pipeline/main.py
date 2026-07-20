"""[Day 1] 종합 실습 - 실무형 수집·검증·품질 파이프라인.

작성자 : 신주용 (광주 3반)

프로그램 설명
- 3개 공개 API 를 비동기로 동시 수집 → 필드 추출 → Pydantic v2 검증
  → 검증 통과 데이터를 CSV·Parquet 로 저장하고 읽기/쓰기 성능 비교

흐름
1) collect_all() : asyncio + httpx 로 3개 API 동시 수집 (asyncio.gather)
2) build/validate : 필요한 필드 추출 후 Pydantic 모델로 타입·범위 검증
3) save_and_benchmark() : CSV·Parquet 저장 + 성능 측정 결과 출력

실행 : python -m pipeline.main

변경 이력
- 2026-07-20 최초 작성
- 2026-07-20 패키지(pipeline/) 구조로 재구성
"""

import asyncio
from pathlib import Path

import httpx
from pydantic import ValidationError

from pipeline.collector import collect_all
from pipeline.models import CountryInfo, IpInfo, WeatherHour
from pipeline.storage import save_and_benchmark

# 산출물은 레포 루트의 output/ 에 저장 (패키지 밖)
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def build_weather_records(weather_json: dict) -> list[dict]:
    """Open-Meteo hourly 3배열(time/기온/강수확률)을 시간별 레코드로 변환.

    입력 : weather_json - Open-Meteo 원시 JSON
    반환 : {time, temperature, precipitation_probability} 리스트
    """
    h = weather_json["hourly"]
    return [
        {"time": t, "temperature": temp, "precipitation_probability": p}
        for t, temp, p in zip(
            h["time"], h["temperature_2m"], h["precipitation_probability"]
        )
    ]


def validate_weather(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """시간별 레코드를 WeatherHour 로 검증해 정상/오류 분리.

    입력 : records - build_weather_records 결과
    반환 : (valid, errors) - valid 는 model_dump dict, errors 는 {row, error}
    """
    valid, errors = [], []
    for i, row in enumerate(records):
        try:
            valid.append(WeatherHour(**row).model_dump())
        except ValidationError as e:
            errors.append({"row": i, "error": e.errors()[0]["msg"]})
    return valid, errors


def main() -> None:
    """수집 → 검증 → 저장/성능비교 전체 파이프라인 실행."""
    # 1) 비동기 수집 - 실패 시 안내 후 종료
    try:
        raw = asyncio.run(collect_all())
    except (RuntimeError, httpx.HTTPError) as e:
        print(f"[오류] API 수집 실패: {e}")
        return
    print("1) 비동기 수집 완료 : weather / country / ip 3종")

    # 2) 검증 - 날씨(다건) + 국가/IP(단건)
    weather_records = build_weather_records(raw["weather"])
    valid, errors = validate_weather(weather_records)
    print(f"2) 날씨 검증 : 정상 {len(valid)}건 / 오류 {len(errors)}건")

    try:
        c = raw["country"]
        country = CountryInfo(
            name=c["name"], capital=c["capital"], region=c["region"],
            population=c["population"], code=c["alpha3Code"],
        )
        print(f"   국가 : {country.name} / 수도 {country.capital}"
              f" / 인구 {country.population:,}")
    except (ValidationError, KeyError) as e:
        print(f"   국가 검증 실패 : {e}")

    try:
        keys = ("status", "country", "city", "lat", "lon", "timezone", "query")
        ip = IpInfo(**{k: raw["ip"].get(k) for k in keys})
        print(f"   IP {ip.query} : {ip.country}/{ip.city} ({ip.timezone})")
    except ValidationError as e:
        print(f"   IP 검증 실패 : {e}")

    # 3) 저장 + 성능 비교 (검증 통과한 날씨 데이터 기준)
    bench = save_and_benchmark(valid, OUTPUT_DIR)
    print("3) 저장/성능 비교 (weather 데이터):")
    for fmt, m in bench.items():
        print(f"   {fmt:<7} | 쓰기 {m['write_ms']:>6}ms | 읽기"
              f" {m['read_ms']:>6}ms | 크기 {m['size_bytes']:>6}B")
    print("파이프라인 완료")


if __name__ == "__main__":
    main()


# 실행 결과 (샘플 - 날씨·IP 값은 실행 시점마다 달라짐)
# ------------------------------------------------------------
# 1) 비동기 수집 완료 : weather / country / ip 3종
# 2) 날씨 검증 : 정상 72건 / 오류 0건
#    국가 : Korea (Republic of) / 수도 Seoul / 인구 51,780,579
#    IP 8.8.8.8 : United States/Ashburn (America/New_York)
# 3) 저장/성능 비교 (weather 데이터):
#    csv     | 쓰기  0.174ms | 읽기  0.198ms | 크기   1849B
#    parquet | 쓰기  0.292ms | 읽기  0.417ms | 크기   3415B
# 파이프라인 완료
