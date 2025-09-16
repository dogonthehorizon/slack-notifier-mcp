#!/usr/bin/env python3
"""
Simple test script to demonstrate the slack-progress-update tool.

This script shows how to use the updated tool that sends messages to a
pre-configured channel specified by environment variables.

Usage:
    # Set required environment variables first
    export SLACK_BOT_TOKEN="xoxb-your-bot-token"
    export SLACK_CHANNEL="general"

    # Then run the test
    python test_tool.py
"""

import asyncio
import os
import sys
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import TextContent

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


async def test_tool():
    """Test the slack-progress-update tool with various scenarios."""

    print("🧪 Testing Slack Progress Update Tool")
    print("=" * 50)

    # Check environment variables
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    channel = os.getenv("SLACK_CHANNEL")

    if not bot_token or not channel:
        print("❌ Missing required environment variables!")
        print("Please set:")
        print("  export SLACK_BOT_TOKEN='xoxb-your-bot-token'")
        print("  export SLACK_CHANNEL='your-channel-name'")
        return

    print(f"✅ Bot token configured: {bot_token[:20]}...")
    print(f"✅ Channel configured: {channel}")
    print()

    # Configure server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "slack_notifier_mcp.server"],
        env=dict(os.environ),
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize connection
                await session.initialize()
                print("✅ Connected to MCP server")

                # List available tools
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                print(f"📋 Available tools: {tool_names}")

                if "slack-progress-update" not in tool_names:
                    print("❌ slack-progress-update tool not found!")
                    return

                print()
                print("🚀 Running test scenarios...")
                print("-" * 30)

                # Test scenarios
                test_cases = [
                    {
                        "name": "Basic completion",
                        "args": {
                            "summary": "Successfully processed customer data batch",
                            "status": "completed",
                        },
                    },
                    {
                        "name": "Detailed success with agent info",
                        "args": {
                            "summary": "Machine learning model training completed",
                            "details": "Trained on 10K samples, achieved 95% accuracy, saved model to production",
                            "status": "success",
                            "task_id": "ML-TRAIN-001",
                            "agent_name": "MLTrainingAgent",
                        },
                    },
                    {
                        "name": "Error notification",
                        "args": {
                            "summary": "Database connection failed",
                            "details": "Connection timeout after 30 seconds. Will retry with exponential backoff.",
                            "status": "failed",
                            "agent_name": "DatabaseAgent",
                            "task_id": "DB-SYNC-456",
                        },
                    },
                    {
                        "name": "Progress update",
                        "args": {
                            "summary": "Long-running data analysis in progress",
                            "details": "Processed 2,500/10,000 records (25% complete). ETA: 2 hours.",
                            "status": "in_progress",
                            "agent_name": "DataAnalysisAgent",
                        },
                    },
                ]

                for i, test_case in enumerate(test_cases, 1):
                    print(f"\n📝 Test {i}: {test_case['name']}")

                    try:
                        result = await session.call_tool(
                            "slack-progress-update", test_case["args"]
                        )

                        if result.content and len(result.content) > 0:
                            content = result.content[0]
                            if isinstance(content, TextContent):
                                print(f"   ✅ {content.text}")
                            else:
                                print(f"   ✅ Success: {content}")
                        else:
                            print("   ✅ Message sent successfully")

                    except Exception as e:
                        print(f"   ❌ Failed: {str(e)}")

                    # Small delay between messages
                    await asyncio.sleep(1)

                print("\n" + "=" * 50)
                print("🎉 Test completed! Check your Slack channel for messages.")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure both SLACK_BOT_TOKEN and SLACK_CHANNEL are set")
        print("2. Verify bot token is valid and starts with 'xoxb-'")
        print("3. Make sure bot is added to the configured channel")
        print("4. Check that bot has 'chat:write' permission")


def main():
    """Main entry point."""
    try:
        asyncio.run(test_tool())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
