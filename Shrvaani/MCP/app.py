#!/usr/bin/env python3
"""
MCP Client Application for Airbnb and Playwright integration
"""

import json
import subprocess
import sys
from typing import Any, Optional
from datetime import datetime


class MCPClient:
    """Client to interact with MCP servers"""
    
    def __init__(self, config_file: str = "browser_mcp.json"):
        """Initialize MCP client with configuration"""
        self.config = self._load_config(config_file)
        self.servers = {}
    
    def _load_config(self, config_file: str) -> dict:
        """Load MCP configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"✓ Loaded configuration from {config_file}")
            return config
        except FileNotFoundError:
            print(f"✗ Configuration file {config_file} not found")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"✗ Invalid JSON in {config_file}")
            sys.exit(1)
    
    def get_servers(self) -> dict:
        """Get available MCP servers from configuration"""
        servers = self.config.get("mcpServers", {})
        print(f"\n📋 Available MCP Servers:")
        for server_name, server_config in servers.items():
            if isinstance(server_config, dict) and "command" in server_config:
                print(f"  • {server_name}: {server_config.get('command')}")
        return servers
    
    def search_airbnb(self, location: str, check_in: str, checkout: Optional[str] = None) -> dict:
        """
        Search for Airbnb listings
        
        Args:
            location: Location to search (e.g., "Trissure")
            check_in: Check-in date (e.g., "2026-01-23")
            checkout: Check-out date (optional)
        
        Returns:
            Search results dictionary
        """
        print(f"\n🔍 Searching Airbnb for listings in {location}...")
        print(f"   Check-in: {check_in}")
        
        search_params = {
            "location": location,
            "checkInDate": check_in,
        }
        
        if checkout:
            search_params["checkOutDate"] = checkout
            print(f"   Check-out: {checkout}")
        
        # This would be called via MCP protocol in a real implementation
        print(f"   Parameters: {search_params}")
        
        return {
            "status": "pending",
            "message": "Airbnb MCP server would process this request",
            "params": search_params
        }
    
    def display_config(self) -> None:
        """Display the full configuration"""
        print("\n📄 Configuration Details:")
        print(json.dumps(self.config, indent=2))


def main():
    """Main application entry point"""
    print("=" * 50)
    print("MCP Browser & Airbnb Client")
    print("=" * 50)
    
    # Initialize MCP client
    client = MCPClient()
    
    # Display available servers
    servers = client.get_servers()
    
    # Display full configuration
    client.display_config()
    
    # Example search
    print("\n" + "=" * 50)
    print("Example Airbnb Search")
    print("=" * 50)
    
    results = client.search_airbnb(
        location="Trissure",
        check_in="2026-01-23",
        checkout="2026-01-25"
    )
    
    print(f"\nSearch Results:")
    print(json.dumps(results, indent=2))
    
    # Interactive mode
    print("\n" + "=" * 50)
    print("Interactive Search")
    print("=" * 50)
    
    try:
        location = input("\nEnter location (or press Enter for 'Trissure'): ").strip() or "Trissure"
        check_in = input("Enter check-in date (YYYY-MM-DD, or press Enter for '2026-01-23'): ").strip() or "2026-01-23"
        checkout = input("Enter check-out date (YYYY-MM-DD, optional): ").strip() or None
        
        results = client.search_airbnb(location, check_in, checkout)
        print(f"\nSearch Results:")
        print(json.dumps(results, indent=2))
        
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
