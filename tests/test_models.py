"""models 스키마 검증 단위 테스트 (pytest) - 네트워크 없이 실행.

작성자 : 신주용 (광주 3반)

변경 이력
- 2026-07-20 최초 작성
"""

import pytest
from pydantic import ValidationError

from pipeline.models import CountryInfo, IpInfo, WeatherHour


def test_weather_valid():
    """정상 값은 검증 통과."""
    r = WeatherHour(
        time="2026-07-20T00:00", temperature=23.2,
        precipitation_probability=6,
    )
    assert r.temperature == 23.2


def test_weather_precip_out_of_range():
    """강수확률 범위(0~100) 초과 시 ValidationError."""
    with pytest.raises(ValidationError):
        WeatherHour(
            time="2026-07-20T00:00", temperature=23.2,
            precipitation_probability=150,
        )


def test_weather_bad_type():
    """기온에 숫자 아닌 값 → ValidationError."""
    with pytest.raises(ValidationError):
        WeatherHour(
            time="t", temperature="hot", precipitation_probability=10,
        )


def test_country_population_positive():
    """인구 0 이하 → ValidationError."""
    with pytest.raises(ValidationError):
        CountryInfo(
            name="Korea", capital="Seoul", region="Asia",
            population=0, code="KOR",
        )


def test_ip_lat_range():
    """위도 범위(-90~90) 초과 → ValidationError."""
    with pytest.raises(ValidationError):
        IpInfo(
            status="success", country="US", city="Ashburn",
            lat=999, lon=-77.5, timezone="America/New_York",
            query="8.8.8.8",
        )
