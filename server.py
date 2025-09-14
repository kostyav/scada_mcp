#!/usr/bin/env python3
"""
SCADA-LTS MCP Server

A Model Context Protocol server for interacting with SCADA-LTS (Supervisory Control and Data Acquisition)
system. This MCP provides tools to manage data sources, data points, alarms, and real-time data.

Based on SCADA-LTS: https://github.com/SCADA-LTS/Scada-LTS
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urljoin

import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest,
    Prompt,
    PromptArgument,
    PromptMessage,
    UserMessage,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scada-lts-mcp")


class ScadaLTSClient:
    """Client for interacting with SCADA-LTS REST API"""

    def __init__(self, base_url: str, username: str = "", password: str = ""):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session_token = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def authenticate(self) -> bool:
        """Authenticate with SCADA-LTS system"""
        if not self.username or not self.password:
            logger.warning("No credentials provided, using guest access")
            return True

        auth_url = f"{self.base_url}/api/auth/login"
        try:
            response = await self.client.post(
                auth_url,
                json={"username": self.username, "password": self.password}
            )
            if response.status_code == 200:
                data = response.json()
                self.session_token = data.get("token")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {"Content-Type": "application/json"}
        if self.session_token:
            headers["Authorization"] = f"Bearer {self.session_token}"
        return headers

    async def get_data_sources(self) -> List[Dict[str, Any]]:
        """Get all data sources"""
        url = f"{self.base_url}/api/datasources"
        try:
            response = await self.client.get(url, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting data sources: {e}")
            return []

    async def get_data_points(self, data_source_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get data points, optionally filtered by data source ID"""
        url = f"{self.base_url}/api/datapoints"
        if data_source_id:
            url += f"?dataSourceId={data_source_id}"

        try:
            response = await self.client.get(url, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting data points: {e}")
            return []

    async def get_point_value(self, point_id: int) -> Optional[Dict[str, Any]]:
        """Get current value of a data point"""
        url = f"{self.base_url}/api/point-values/{point_id}/latest"
        try:
            response = await self.client.get(url, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting point value: {e}")
            return None

    async def set_point_value(self, point_id: int, value: Any) -> bool:
        """Set value of a settable data point"""
        url = f"{self.base_url}/api/point-values/{point_id}/set"
        try:
            response = await self.client.post(
                url,
                json={"value": value},
                headers=self._get_headers()
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error setting point value: {e}")
            return False

    async def get_alarms(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get system alarms"""
        url = f"{self.base_url}/api/alarms"
        if active_only:
            url += "?active=true"

        try:
            response = await self.client.get(url, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting alarms: {e}")
            return []

    async def acknowledge_alarm(self, alarm_id: int) -> bool:
        """Acknowledge an alarm"""
        url = f"{self.base_url}/api/alarms/{alarm_id}/ack"
        try:
            response = await self.client.post(url, headers=self._get_headers())
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error acknowledging alarm: {e}")
            return False

    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status information"""
        url = f"{self.base_url}/api/system/status"
        try:
            response = await self.client.get(url, headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "unknown", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"status": "error", "error": str(e)}


# Global SCADA-LTS client instance
scada_client: Optional[ScadaLTSClient] = None

# Create MCP server instance
server = Server("scada-lts-mcp")


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available SCADA-LTS tools"""
    return [
        Tool(
            name="get_data_sources",
            description="Get all data sources from SCADA-LTS system",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_data_points",
            description="Get data points from SCADA-LTS system, optionally filtered by data source ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_source_id": {
                        "type": "integer",
                        "description": "Optional data source ID to filter data points"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_point_value",
            description="Get current value of a specific data point",
            inputSchema={
                "type": "object",
                "properties": {
                    "point_id": {
                        "type": "integer",
                        "description": "ID of the data point to read"
                    }
                },
                "required": ["point_id"]
            }
        ),
        Tool(
            name="set_point_value",
            description="Set value of a settable data point",
            inputSchema={
                "type": "object",
                "properties": {
                    "point_id": {
                        "type": "integer",
                        "description": "ID of the data point to write to"
                    },
                    "value": {
                        "description": "Value to write (number, boolean, or string)"
                    }
                },
                "required": ["point_id", "value"]
            }
        ),
        Tool(
            name="get_alarms",
            description="Get system alarms",
            inputSchema={
                "type": "object",
                "properties": {
                    "active_only": {
                        "type": "boolean",
                        "description": "Whether to return only active alarms (default: true)",
                        "default": True
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="acknowledge_alarm",
            description="Acknowledge an alarm",
            inputSchema={
                "type": "object",
                "properties": {
                    "alarm_id": {
                        "type": "integer",
                        "description": "ID of the alarm to acknowledge"
                    }
                },
                "required": ["alarm_id"]
            }
        ),
        Tool(
            name="get_system_status",
            description="Get SCADA-LTS system status information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="configure_connection",
            description="Configure connection to SCADA-LTS system",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_url": {
                        "type": "string",
                        "description": "Base URL of SCADA-LTS system (e.g., http://localhost:8080/Scada-LTS)"
                    },
                    "username": {
                        "type": "string",
                        "description": "Username for authentication (optional)"
                    },
                    "password": {
                        "type": "string",
                        "description": "Password for authentication (optional)"
                    }
                },
                "required": ["base_url"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    global scada_client

    try:
        if name == "configure_connection":
            base_url = arguments["base_url"]
            username = arguments.get("username", "")
            password = arguments.get("password", "")

            scada_client = ScadaLTSClient(base_url, username, password)

            # Test authentication
            auth_success = await scada_client.authenticate()

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Connection configured for {base_url}. "
                             f"Authentication: {'successful' if auth_success else 'failed or guest mode'}"
                    )
                ]
            )

        # Check if client is configured
        if not scada_client:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="SCADA-LTS client not configured. Please use configure_connection tool first."
                    )
                ]
            )

        if name == "get_data_sources":
            data_sources = await scada_client.get_data_sources()
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Found {len(data_sources)} data sources:\n" +
                             json.dumps(data_sources, indent=2)
                    )
                ]
            )

        elif name == "get_data_points":
            data_source_id = arguments.get("data_source_id")
            data_points = await scada_client.get_data_points(data_source_id)
            filter_text = f" for data source {data_source_id}" if data_source_id else ""
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Found {len(data_points)} data points{filter_text}:\n" +
                             json.dumps(data_points, indent=2)
                    )
                ]
            )

        elif name == "get_point_value":
            point_id = arguments["point_id"]
            value = await scada_client.get_point_value(point_id)
            if value is not None:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Point {point_id} value:\n" +
                            json.dumps(value, indent=2)
                        )
                    ]
                )
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Could not retrieve value for point {point_id}"
                        )
                    ]
                )

        elif name == "set_point_value":
            point_id = arguments["point_id"]
            value = arguments["value"]
            success = await scada_client.set_point_value(point_id, value)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Setting point {point_id} to {value}: {'successful' if success else 'failed'}"
                    )
                ]
            )

        elif name == "get_alarms":
            active_only = arguments.get("active_only", True)
            alarms = await scada_client.get_alarms(active_only)
            alarm_type = "active" if active_only else "all"
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Found {len(alarms)} {alarm_type} alarms:\n" +
                             json.dumps(alarms, indent=2)
                    )
                ]
            )

        elif name == "acknowledge_alarm":
            alarm_id = arguments["alarm_id"]
            success = await scada_client.acknowledge_alarm(alarm_id)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Acknowledging alarm {alarm_id}: {'successful' if success else 'failed'}"
                    )
                ]
            )

        elif name == "get_system_status":
            status = await scada_client.get_system_status()
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"System status:\n" + json.dumps(status, indent=2)
                    )
                ]
            )

        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )
                ]
            )

    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )
            ]
        )


@server.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List available prompts"""
    return [
        Prompt(
            name="scada_system_overview",
            description="Get a comprehensive overview of the SCADA-LTS system",
            arguments=[
                PromptArgument(
                    name="include_alarms",
                    description="Whether to include alarm information",
                    required=False
                )
            ]
        ),
        Prompt(
            name="data_point_analysis",
            description="Analyze data points for a specific data source",
            arguments=[
                PromptArgument(
                    name="data_source_id",
                    description="ID of the data source to analyze",
                    required=True
                )
            ]
        )
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: Dict[str, str]) -> GetPromptResult:
    """Handle prompt requests"""
    global scada_client

    if not scada_client:
        return GetPromptResult(
            description="SCADA-LTS client not configured",
            messages=[
                UserMessage(
                    content="Please configure SCADA-LTS connection first using the configure_connection tool."
                )
            ]
        )

    if name == "scada_system_overview":
        include_alarms = arguments.get(
            "include_alarms", "false").lower() == "true"

        # Gather system information
        data_sources = await scada_client.get_data_sources()
        data_points = await scada_client.get_data_points()
        system_status = await scada_client.get_system_status()

        content = f"""# SCADA-LTS System Overview

## System Status
{json.dumps(system_status, indent=2)}

## Data Sources ({len(data_sources)} total)
{json.dumps(data_sources, indent=2)}

## Data Points ({len(data_points)} total)
{json.dumps(data_points, indent=2)}
"""

        if include_alarms:
            alarms = await scada_client.get_alarms()
            content += f"""
## Active Alarms ({len(alarms)} total)
{json.dumps(alarms, indent=2)}
"""

        return GetPromptResult(
            description="SCADA-LTS system overview",
            messages=[
                UserMessage(content=content)
            ]
        )

    elif name == "data_point_analysis":
        data_source_id = int(arguments["data_source_id"])

        # Get data source information
        data_sources = await scada_client.get_data_sources()
        target_ds = next(
            (ds for ds in data_sources if ds.get("id") == data_source_id), None)

        if not target_ds:
            return GetPromptResult(
                description="Data source not found",
                messages=[
                    UserMessage(
                        content=f"Data source with ID {data_source_id} not found.")
                ]
            )

        # Get data points for this data source
        data_points = await scada_client.get_data_points(data_source_id)

        # Get current values for data points
        point_values = {}
        for dp in data_points:
            point_id = dp.get("id")
            if point_id:
                value = await scada_client.get_point_value(point_id)
                point_values[point_id] = value

        content = f"""# Data Source Analysis: {target_ds.get('name', 'Unknown')}

## Data Source Details
{json.dumps(target_ds, indent=2)}

## Data Points ({len(data_points)} total)
{json.dumps(data_points, indent=2)}

## Current Values
{json.dumps(point_values, indent=2)}
"""

        return GetPromptResult(
            description=f"Analysis of data source {data_source_id}",
            messages=[
                UserMessage(content=content)
            ]
        )

    else:
        return GetPromptResult(
            description="Unknown prompt",
            messages=[
                UserMessage(content=f"Unknown prompt: {name}")
            ]
        )


async def main():
    """Main entry point"""
    # Import here to avoid issues if mcp package is not available
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="scada-lts-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
