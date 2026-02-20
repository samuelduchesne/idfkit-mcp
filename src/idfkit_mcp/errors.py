"""Unified error formatting for MCP tool responses."""

from __future__ import annotations

from typing import Any


def format_error(error: Exception) -> dict[str, Any]:
    """Convert an exception into a structured error dict for tool responses."""
    from idfkit.exceptions import (
        DuplicateObjectError,
        EnergyPlusNotFoundError,
        SchemaNotFoundError,
        SimulationError,
        UnknownObjectTypeError,
        ValidationFailedError,
        VersionNotFoundError,
    )

    if isinstance(error, ValidationFailedError):
        return {"error": "Validation failed", "details": str(error)}
    if isinstance(error, KeyError):
        return {"error": f"Not found: {error}"}
    if isinstance(error, EnergyPlusNotFoundError):
        return {
            "error": "EnergyPlus not found",
            "suggestion": "Install EnergyPlus or set the ENERGYPLUS_DIR environment variable.",
        }
    if isinstance(error, SchemaNotFoundError):
        return {"error": f"Schema not found: {error}"}
    if isinstance(error, VersionNotFoundError):
        return {"error": f"Version not found: {error}"}
    if isinstance(error, UnknownObjectTypeError):
        return {"error": f"Unknown object type: {error}"}
    if isinstance(error, DuplicateObjectError):
        return {"error": f"Duplicate object: {error}"}
    if isinstance(error, SimulationError):
        return {"error": f"Simulation error: {error}"}
    if isinstance(error, RuntimeError):
        return {"error": str(error)}
    return {"error": f"{type(error).__name__}: {error}"}
