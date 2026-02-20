"""Tests for weather tools."""

from __future__ import annotations


def _tool(name: str):  # noqa: ANN202
    from idfkit_mcp.server import mcp

    return mcp._tool_manager._tools[name]


class TestSearchWeatherStations:
    def test_text_search(self) -> None:
        result = _tool("search_weather_stations").fn(query="Chicago")
        assert result["search_type"] == "text"
        assert result["count"] > 0

    def test_spatial_search(self) -> None:
        result = _tool("search_weather_stations").fn(latitude=41.88, longitude=-87.63)
        assert result["search_type"] == "spatial"
        assert result["count"] > 0

    def test_no_params(self) -> None:
        result = _tool("search_weather_stations").fn()
        assert "error" in result

    def test_country_filter(self) -> None:
        result = _tool("search_weather_stations").fn(query="Chicago", country="USA")
        assert result["count"] > 0
        for station in result["stations"]:
            assert station["country"].upper() == "USA"
