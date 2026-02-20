"""Tests for schema exploration tools."""

from __future__ import annotations

from idfkit_mcp.tools.schema import _parse_version, register
from mcp.server.fastmcp import FastMCP


def _make_server() -> FastMCP:
    mcp = FastMCP("test")
    register(mcp)
    return mcp


class TestParseVersion:
    def test_none(self) -> None:
        assert _parse_version(None) is None

    def test_valid(self) -> None:
        assert _parse_version("24.1.0") == (24, 1, 0)

    def test_invalid(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="X.Y.Z"):
            _parse_version("24.1")


class TestListObjectTypes:
    def test_returns_groups(self) -> None:
        from idfkit_mcp.server import mcp

        tool = mcp._tool_manager._tools["list_object_types"]
        result = tool.fn()
        assert "total_types" in result
        assert result["total_types"] > 0
        assert "groups" in result

    def test_filter_by_group(self) -> None:
        from idfkit_mcp.server import mcp

        tool = mcp._tool_manager._tools["list_object_types"]
        result = tool.fn(group="Thermal Zones and Surfaces")
        assert result["total_types"] > 0
        # All returned items should be in the filtered group
        assert "Thermal Zones and Surfaces" in result["groups"]

    def test_returns_error_for_bad_version(self) -> None:
        from idfkit_mcp.server import mcp

        tool = mcp._tool_manager._tools["list_object_types"]
        result = tool.fn(version="1.0.0")
        assert "error" in result


class TestDescribeObjectType:
    def test_zone(self) -> None:
        from idfkit_mcp.server import mcp

        tool = mcp._tool_manager._tools["describe_object_type"]
        result = tool.fn(object_type="Zone")
        assert result["object_type"] == "Zone"
        assert result["has_name"] is True
        assert len(result["fields"]) > 0
        field_names = [f["name"] for f in result["fields"]]
        assert "x_origin" in field_names

    def test_unknown_type(self) -> None:
        from idfkit_mcp.server import mcp

        tool = mcp._tool_manager._tools["describe_object_type"]
        result = tool.fn(object_type="NonExistent")
        assert "error" in result


class TestSearchSchema:
    def test_search_zone(self) -> None:
        from idfkit_mcp.server import mcp

        tool = mcp._tool_manager._tools["search_schema"]
        result = tool.fn(query="Zone")
        assert result["count"] > 0
        types = [m["object_type"] for m in result["matches"]]
        assert "Zone" in types

    def test_search_no_results(self) -> None:
        from idfkit_mcp.server import mcp

        tool = mcp._tool_manager._tools["search_schema"]
        result = tool.fn(query="xyznonexistent123")
        assert result["count"] == 0


class TestGetAvailableReferences:
    def test_without_model(self) -> None:
        from idfkit_mcp.server import mcp

        tool = mcp._tool_manager._tools["get_available_references"]
        result = tool.fn(object_type="BuildingSurface:Detailed", field_name="zone_name")
        assert "error" in result

    def test_with_model(self, state_with_zones: object) -> None:
        from idfkit_mcp.server import mcp

        tool = mcp._tool_manager._tools["get_available_references"]
        result = tool.fn(object_type="BuildingSurface:Detailed", field_name="zone_name")
        assert "available_names" in result
        assert "Office" in result["available_names"]
        assert "Corridor" in result["available_names"]

    def test_non_reference_field(self, state_with_model: object) -> None:
        from idfkit_mcp.server import mcp

        tool = mcp._tool_manager._tools["get_available_references"]
        result = tool.fn(object_type="Zone", field_name="x_origin")
        assert "error" in result
