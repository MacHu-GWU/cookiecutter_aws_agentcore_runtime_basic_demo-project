# -*- coding: utf-8 -*-

"""
Debug client of the local PowerPlantMcp server (``mise run ac-local-mcp``):
list its tools, then call ``get_site`` for site S-03.
"""

import json
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_URL = "http://localhost:8000/mcp"


async def main():
    async with streamable_http_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            for tool in result.tools:
                print(f"tool: {tool.name}")
            result = await session.call_tool("get_site", {"site_id": "S-03"})
            site = json.loads(result.content[0].text)
            print(json.dumps(site, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
