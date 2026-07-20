"""비동기 API 수집 - asyncio + httpx 로 3개 API 동시 호출.

작성자 : 신주용 (광주 3반)

- Open-Meteo : 서울 3일 시간대별 기온·강수확률
- Countries.dev : 한국 국가 정보
- ip-api : IP 기반 지역 정보

변경 이력
- 2026-07-20 최초 작성
"""

import asyncio

import httpx

# API 엔드포인트
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=37.5665&longitude=126.9780"
    "&hourly=temperature_2m,precipitation_probability"
    "&forecast_days=3&timezone=Asia/Seoul"
)
COUNTRY_URL = "https://countries.dev/alpha/KOR"
IP_URL = "http://ip-api.com/json/8.8.8.8"

TIMEOUT = 10.0  # 초


async def _fetch_json(client: httpx.AsyncClient, url: str) -> dict:
    """단일 URL 을 GET 해 JSON(dict) 반환.

    입력 : client - httpx 비동기 클라이언트, url - 요청 주소
    반환 : 파싱된 JSON dict
    예외 : HTTP 오류/타임아웃은 httpx 예외로 전파 (상위 gather 에서 처리)
    """
    resp = await client.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


async def collect_all() -> dict:
    """3개 API 를 asyncio.gather 로 동시 수집.

    반환 : {"weather", "country", "ip"} 원시 JSON dict
    예외 : 개별 실패는 return_exceptions 로 모은 뒤, 어떤 API 가 실패했는지
           RuntimeError 로 다시 던짐
    """
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            _fetch_json(client, WEATHER_URL),
            _fetch_json(client, COUNTRY_URL),
            _fetch_json(client, IP_URL),
            return_exceptions=True,  # 일부 실패해도 나머지 결과 확보
        )

    raw = {}
    for key, result in zip(("weather", "country", "ip"), results):
        if isinstance(result, Exception):
            raise RuntimeError(f"{key} 수집 실패: {result}") from result
        raw[key] = result
    return raw
