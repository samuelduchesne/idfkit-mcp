"""Model reading and inspection tools."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from mcp.server.fastmcp import FastMCP

from idfkit_mcp.errors import format_error
from idfkit_mcp.serializers import serialize_object
from idfkit_mcp.state import get_state


def _safe_tool(func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
    """Convert exceptions into MCP-friendly error dicts."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return format_error(e)

    return wrapper


def register(mcp: FastMCP) -> None:
    """Register read tools on the MCP server."""
    mcp.tool()(load_model)
    mcp.tool()(get_model_summary)
    mcp.tool()(list_objects)
    mcp.tool()(get_object)
    mcp.tool()(search_objects)
    mcp.tool()(get_references)


@_safe_tool
def load_model(file_path: str, version: str | None = None) -> dict[str, Any]:
    """Load an IDF or epJSON file as the active model.

    Auto-detects format by file extension (.idf or .epjson/.json).

    Args:
        file_path: Path to the IDF or epJSON file.
        version: Optional version override as "X.Y.Z".
    """
    from pathlib import Path

    from idfkit import load_epjson, load_idf

    state = get_state()
    path = Path(file_path)
    ver = None
    if version is not None:
        parts = version.split(".")
        ver = (int(parts[0]), int(parts[1]), int(parts[2]))

    if path.suffix.lower() in (".epjson", ".json"):
        doc = load_epjson(str(path), version=ver)
    else:
        doc = load_idf(str(path), version=ver)

    state.document = doc
    state.schema = doc.schema
    state.file_path = path
    state.simulation_result = None

    return _build_summary(doc, state)


@_safe_tool
def get_model_summary() -> dict[str, Any]:
    """Get a summary of the currently loaded model.

    Returns version, total objects, zone count, and counts by group/type.
    """
    state = get_state()
    doc = state.require_model()
    return _build_summary(doc, state)


@_safe_tool
def list_objects(object_type: str, limit: int = 50) -> dict[str, Any]:
    """List objects of a given type from the loaded model.

    Returns object names and required field values in brief format.

    Args:
        object_type: The EnergyPlus object type (e.g. "Zone").
        limit: Maximum number of objects to return (default 50).
    """
    state = get_state()
    doc = state.require_model()

    if object_type not in doc:
        return {"error": f"No objects of type '{object_type}' in the model."}

    collection = doc[object_type]
    total = len(collection)
    objects = [serialize_object(obj, schema=state.schema, brief=True) for obj in list(collection)[:limit]]

    return {"object_type": object_type, "total": total, "returned": len(objects), "objects": objects}


@_safe_tool
def get_object(object_type: str, name: str) -> dict[str, Any]:
    """Get all field values for a specific object.

    Args:
        object_type: The EnergyPlus object type.
        name: The object name.
    """
    state = get_state()
    doc = state.require_model()

    if object_type not in doc:
        return {"error": f"No objects of type '{object_type}' in the model."}

    collection = doc[object_type]
    obj = collection.get(name)
    if obj is None:
        return {"error": f"Object '{name}' not found in '{object_type}'."}

    return serialize_object(obj)


@_safe_tool
def search_objects(query: str, object_type: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Search for objects by name or field values.

    Args:
        query: Search string (case-insensitive substring match on name and string fields).
        object_type: Optionally restrict search to a specific type.
        limit: Maximum results to return (default 20).
    """
    state = get_state()
    doc = state.require_model()
    query_lower = query.lower()

    matches: list[dict[str, Any]] = []
    for obj in doc.all_objects:
        if object_type is not None and obj.obj_type != object_type:
            continue
        if _matches_query(obj, query_lower):
            matches.append({"object_type": obj.obj_type, "name": obj.name})
            if len(matches) >= limit:
                break

    return {"query": query, "count": len(matches), "matches": matches}


@_safe_tool
def get_references(name: str) -> dict[str, Any]:
    """Get bidirectional references for an object name.

    Returns objects that reference this name, and names this object references.

    Args:
        name: The object name to check references for.
    """
    state = get_state()
    doc = state.require_model()

    # Objects that reference this name
    referencing = doc.get_referencing(name)
    referenced_by = [{"object_type": obj.obj_type, "name": obj.name} for obj in referencing]

    # Find the object and get what it references
    references: list[str] = []
    target_obj = _find_object_by_name(doc, name)
    if target_obj is not None:
        refs = doc.get_references(target_obj)
        references = sorted(refs)

    return {
        "name": name,
        "referenced_by": referenced_by,
        "referenced_by_count": len(referenced_by),
        "references": references,
        "references_count": len(references),
    }


def _build_summary(doc: Any, state: Any) -> dict[str, Any]:
    """Build a model summary dict."""
    from idfkit import version_string

    groups: dict[str, dict[str, int]] = {}
    total_objects = 0
    zone_count = 0

    for obj_type, collection in doc.items():
        count = len(collection)
        total_objects += count
        if obj_type == "Zone":
            zone_count = count
        schema = state.schema
        group = schema.get_group(obj_type) if schema else "Unknown"
        group = group or "Ungrouped"
        groups.setdefault(group, {})[obj_type] = count

    return {
        "version": version_string(doc.version),
        "file_path": str(state.file_path) if state.file_path else None,
        "total_objects": total_objects,
        "zone_count": zone_count,
        "groups": {g: {"count": sum(v.values()), "types": v} for g, v in sorted(groups.items())},
    }


def _matches_query(obj: Any, query_lower: str) -> bool:
    """Check if an object matches a search query."""
    if query_lower in obj.name.lower():
        return True
    return any(isinstance(value, str) and query_lower in value.lower() for value in obj.data.values())


def _find_object_by_name(doc: Any, name: str) -> Any:
    """Find any object by name across all types."""
    for obj in doc.all_objects:
        if obj.name.upper() == name.upper():
            return obj
    return None
