"""Tests for simulation tools."""

from __future__ import annotations

from idfkit_mcp.state import ServerState


def _tool(name: str):  # noqa: ANN202
    from idfkit_mcp.server import mcp

    return mcp._tool_manager._tools[name]


class TestRunSimulation:
    def test_no_model(self) -> None:
        result = _tool("run_simulation").fn()
        assert "error" in result

    def test_no_weather(self, state_with_model: ServerState) -> None:
        result = _tool("run_simulation").fn()
        assert "error" in result


class TestGetResultsSummary:
    def test_no_simulation(self) -> None:
        result = _tool("get_results_summary").fn()
        assert "error" in result


class TestListOutputVariables:
    def test_no_simulation(self) -> None:
        result = _tool("list_output_variables").fn()
        assert "error" in result
