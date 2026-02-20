"""Weather station search and download tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from idfkit_mcp.errors import format_error
from idfkit_mcp.serializers import serialize_station
from idfkit_mcp.state import get_state


def register(mcp: FastMCP) -> None:
    """Register weather tools on the MCP server."""

    @mcp.tool()
    def search_weather_stations(
        query: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        country: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search for weather stations by name/location or coordinates.

        Provide either a text query or latitude/longitude for spatial search.

        Args:
            query: Search text (city, airport code, etc.).
            latitude: Latitude for nearest-station search.
            longitude: Longitude for nearest-station search.
            country: Filter by country code (e.g. "USA").
            limit: Maximum results (default 10).
        """
        try:
            from idfkit.weather import StationIndex

            index = StationIndex.load()

            if latitude is not None and longitude is not None:
                spatial_results = index.nearest(latitude, longitude, limit=limit)
                spatial_stations: list[dict[str, Any]] = []
                for r in spatial_results:
                    if country and r.station.country.upper() != country.upper():
                        continue
                    spatial_stations.append({
                        **serialize_station(r.station),
                        "distance_km": round(r.distance_km, 1),
                    })
                return {
                    "search_type": "spatial",
                    "count": len(spatial_stations),
                    "stations": spatial_stations[:limit],
                }

            if query is not None:
                search_results = index.search(query, limit=limit * 3)
                text_stations: list[dict[str, Any]] = []
                for r in search_results:
                    if country and r.station.country.upper() != country.upper():
                        continue
                    text_stations.append({
                        **serialize_station(r.station),
                        "score": round(r.score, 3),
                        "match_field": r.match_field,
                    })
                    if len(text_stations) >= limit:
                        break
                return {
                    "search_type": "text",
                    "query": query,
                    "count": len(text_stations),
                    "stations": text_stations,
                }

            return {"error": "Provide either 'query' for text search or 'latitude'/'longitude' for spatial search."}
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def download_weather_file(wmo: str | None = None, query: str | None = None) -> dict[str, Any]:
        """Download an EPW weather file for simulation.

        The downloaded file path is stored for reuse with run_simulation.

        Args:
            wmo: WMO station number to download directly.
            query: Search text to find and download the best match.
        """
        try:
            from idfkit.weather import StationIndex, WeatherDownloader

            index = StationIndex.load()

            if query is not None:
                results = index.search(query, limit=1)
                if not results:
                    return {"error": f"No weather stations found for query '{query}'."}
                station = results[0].station
            elif wmo is not None:
                results = index.search(wmo, limit=10)
                station = None
                for r in results:
                    if r.station.wmo == wmo:
                        station = r.station
                        break
                if station is None:
                    return {"error": f"No weather station found with WMO '{wmo}'."}
            else:
                return {"error": "Provide either 'wmo' or 'query' to identify the weather station."}

            downloader = WeatherDownloader()
            files = downloader.download(station)

            state = get_state()
            state.weather_file = files.epw

            return {
                "status": "downloaded",
                "station": serialize_station(station),
                "epw_path": str(files.epw),
                "ddy_path": str(files.ddy),
            }
        except Exception as e:
            return format_error(e)
