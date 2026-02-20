"""FastMCP server for idfkit — EnergyPlus model authoring, validation, and simulation."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from idfkit_mcp.tools import read, schema, simulation, validation, weather, write

mcp = FastMCP(
    "idfkit",
    instructions=(
        "EnergyPlus model editor powered by idfkit. "
        "Create, edit, validate, and simulate building energy models.\n\n"
        "Guidelines:\n"
        "- Use get_model_summary first to understand any loaded model\n"
        "- Call describe_object_type before creating/editing objects to know valid fields\n"
        "- Use batch_add_objects when creating multiple objects (minimizes round-trips)\n"
        "- Validate after modifications with validate_model\n"
        "- For reference fields, use get_available_references to see valid values\n"
        "- Check references before removing objects (remove_object warns by default)"
    ),
)

schema.register(mcp)
read.register(mcp)
write.register(mcp)
validation.register(mcp)
simulation.register(mcp)
weather.register(mcp)


def main() -> None:
    """Run the MCP server with stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
