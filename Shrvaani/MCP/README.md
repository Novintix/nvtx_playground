MCP Learning

## Overview
The integration and usage of Model Context Protocol (MCP) servers with AI agents.
Covered the basic flow of connecting third-party MCP configurations, utilizing them within agents, and testing them via command-line tools.

## Topics Covered

- **MCP Server Creation**: Using MCP inspector for building custom MCP servers
- **Weather MCP Server**: Implemented a weather server that fetches weather alerts for US cities using the National Weather Service API
- **Integration**: Connecting MCP servers to Claude configuration
- **Testing**: Verifying MCP server functionality through the terminal using `app.py`

## Project Structure

mcp_learning/
├── app.py # Main application for testing MCP servers
├── main.py # Additional utilities
├── server/
│ └── weather.py # Custom weather MCP server
├── browser_mcp.json # MCP server configurations
├── pyproject.toml # Project dependencies
└── README.md # This file