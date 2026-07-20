"""Pydantic v2 스키마 - 수집 JSON 의 타입·범위 검증.

작성자 : 신주용 (광주 3반)

- WeatherHour : 시간별 기온·강수확률 (Open-Meteo)
- CountryInfo : 국가 기본 정보 (Countries.dev)
- IpInfo : IP 기반 지역 정보 (ip-api)

변경 이력
- 2026-07-20 최초 작성
"""

from typing import Literal

from pydantic import BaseModel, Field


class WeatherHour(BaseModel):
    """시간별 날씨 레코드 (Open-Meteo hourly).

    - time : 시각 문자열 (ISO8601 형식, 비어있으면 안 됨)
    - temperature : 기온(°C), -90~60 범위
    - precipitation_probability : 강수확률(%), 0~100
    """

    time: str = Field(min_length=1, description="ISO8601 시각")
    temperature: float = Field(ge=-90, le=60, description="기온(°C)")
    precipitation_probability: int = Field(
        ge=0, le=100, description="강수확률(%)"
    )


class CountryInfo(BaseModel):
    """국가 기본 정보 (Countries.dev).

    - name / capital / region : 빈 문자열 불가
    - population : 0 초과
    - code : ISO alpha-3 (3글자)
    """

    name: str = Field(min_length=1, description="국가명")
    capital: str = Field(min_length=1, description="수도")
    region: str = Field(min_length=1, description="대륙/지역")
    population: int = Field(gt=0, description="인구")
    code: str = Field(min_length=3, max_length=3, description="ISO alpha-3")


class IpInfo(BaseModel):
    """IP 기반 지역 정보 (ip-api).

    - status : 'success' 만 허용 (fail 응답은 검증 실패)
    - lat / lon : 위경도 범위 검증
    """

    status: Literal["success"] = Field(description="응답 상태(success 만 허용)")
    country: str = Field(min_length=1, description="국가")
    city: str = Field(min_length=1, description="도시")
    lat: float = Field(ge=-90, le=90, description="위도")
    lon: float = Field(ge=-180, le=180, description="경도")
    timezone: str = Field(min_length=1, description="시간대")
    query: str = Field(min_length=1, description="조회 IP")
