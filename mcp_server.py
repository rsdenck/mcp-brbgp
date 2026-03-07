from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import AnyUrl
import asyncio
import json

from server import (
    initialize_service,
    handle_tool_call,
    get_asn_info,
    get_prefixes,
    get_statistics,
    get_ix_list,
    get_incidents,
    search_asn,
    get_top_asns,
    get_ix_status,
    sync_data_sources,
    get_traffic_stats,
)

app = Server("mcp-brbgp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_asn_info",
            description="Get information about a specific ASN (Autonomous System Number)",
            inputSchema={
                "type": "object",
                "properties": {
                    "asn": {
                        "type": "integer",
                        "description": "The ASN number to look up",
                    }
                },
                "required": ["asn"],
            },
        ),
        Tool(
            name="get_prefixes",
            description="Get all prefixes announced by a specific ASN",
            inputSchema={
                "type": "object",
                "properties": {
                    "asn": {"type": "integer", "description": "The ASN number"}
                },
                "required": ["asn"],
            },
        ),
        Tool(
            name="get_statistics",
            description="Get overall statistics about the Brazilian BGP ecosystem",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_ix_list",
            description="Get list of all Brazilian Internet Exchange Points (IX)",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_incidents",
            description="Get BGP incidents (withdrawals, route leaks, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 50},
                    "incident_type": {
                        "type": "string",
                        "enum": [
                            "withdrawal",
                            "route_leak",
                            "prefix_disappear",
                            "as_fall",
                        ],
                    },
                },
            },
        ),
        Tool(
            name="search_asn",
            description="Search for ASNs by name or number",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (ASN number or name)",
                    }
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_top_asns",
            description="Get top ASNs by number of announced prefixes",
            inputSchema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 10}},
            },
        ),
        Tool(
            name="get_ix_status",
            description="Get current operational status of Brazilian IXs",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="sync_data_sources",
            description="Sync data from PeeringDB and other sources",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_traffic_stats",
            description="Get real-time BGP traffic statistics",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    result = await handle_tool_call(name, arguments)
    return [TextContent(type="text", text=result)]


async def main():
    await initialize_service()

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
