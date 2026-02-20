"""Tests for validation tools."""

from __future__ import annotations

from idfkit_mcp.state import ServerState


def _tool(name: str):
    from idfkit_mcp.server import mcp

    return mcp._tool_manager._tools[name]


class TestValidateModel:
    def test_valid_model(self, state_with_model: ServerState) -> None:
        state_with_model.document.add("Zone", "TestZone")  # type: ignore[union-attr]
        result = _tool("validate_model").fn()
        assert result["is_valid"] is True

    def test_with_zones(self, state_with_zones: ServerState) -> None:
        result = _tool("validate_model").fn()
        assert "is_valid" in result

    def test_filter_by_type(self, state_with_zones: ServerState) -> None:
        result = _tool("validate_model").fn(object_types=["Zone"])
        assert "is_valid" in result

    def test_without_model(self) -> None:
        result = _tool("validate_model").fn()
        assert "error" in result


class TestCheckReferences:
    def test_no_dangling(self, state_with_zones: ServerState) -> None:
        result = _tool("check_references").fn()
        # The surface references "Office" zone which exists
        # construction_name is empty so it shouldn't count as dangling
        assert "dangling_count" in result

    def test_without_model(self) -> None:
        result = _tool("check_references").fn()
        assert "error" in result
