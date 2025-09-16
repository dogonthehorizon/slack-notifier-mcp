#!/usr/bin/env python3
"""
Convenient run script for the Slack Notifier MCP Server.

This script provides an easy way to start the MCP server with proper environment
handling, configuration validation, and helpful error messages.

Usage:
    python run.py [--dev] [--env-file PATH] [--help]

Options:
    --dev           Run in development mode with MCP Inspector
    --env-file      Specify custom .env file path (default: .env)
    --help          Show this help message
"""

import argparse
import os
import sys
from pathlib import Path


def load_env_file(env_file_path: str = ".env") -> bool:
    """
    Load environment variables from a .env file.

    Args:
        env_file_path: Path to the .env file

    Returns:
        True if file was loaded successfully, False otherwise
    """
    env_path = Path(env_file_path)

    if not env_path.exists():
        return False

    try:
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip("\"'")
                    os.environ[key.strip()] = value
        return True
    except Exception as e:
        print(f"⚠️  Warning: Could not load {env_file_path}: {e}")
        return False


def validate_configuration() -> bool:
    """
    Validate that required configuration is present.

    Returns:
        True if configuration is valid, False otherwise
    """
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    channel = os.getenv("SLACK_CHANNEL")

    if not bot_token:
        print(
            "❌ Configuration Error: SLACK_BOT_TOKEN environment variable is not set!"
        )
        print()
        print("To fix this issue:")
        print("1. Create a Slack app and get a bot token:")
        print("   - Go to https://api.slack.com/apps")
        print("   - Create a new app or select an existing one")
        print("   - Go to 'OAuth & Permissions' and add 'chat:write' scope")
        print("   - Install the app to your workspace")
        print("   - Copy the 'Bot User OAuth Token' (starts with xoxb-)")
        print()
        print("2. Set the environment variables:")
        print('   export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"')
        print('   export SLACK_CHANNEL="general"')
        print()
        print("   Or create a .env file:")
        print('   echo "SLACK_BOT_TOKEN=xoxb-your-bot-token-here" > .env')
        print('   echo "SLACK_CHANNEL=general" >> .env')
        print()
        return False

    if not channel:
        print("❌ Configuration Error: SLACK_CHANNEL environment variable is not set!")
        print()
        print("To fix this issue:")
        print("1. Set the channel where notifications will be sent:")
        print('   export SLACK_CHANNEL="general"')
        print()
        print("   Or add to your .env file:")
        print('   echo "SLACK_CHANNEL=general" >> .env')
        print()
        print("2. Make sure the bot is added to the channel:")
        print("   - Go to the Slack channel")
        print("   - Type '/invite @YourBotName' to add the bot")
        print()
        return False

    if not bot_token.startswith(("xoxb-", "xoxp-")):
        print("⚠️  Warning: Bot token doesn't look like a valid Slack bot token")
        print(f"   Current token: {bot_token[:20]}...")
        print("   Expected format: xoxb-... for bot tokens or xoxp-... for user tokens")
        print()

    return True


def run_server(dev_mode: bool = False):
    """
    Run the MCP server.

    Args:
        dev_mode: If True, run with MCP Inspector for development
    """
    # Add src directory to Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))

    if dev_mode:
        print("🚀 Starting Slack Notifier MCP Server in development mode...")
        print("   This will open the MCP Inspector for testing")
        print()

        # Import and run with development server
        try:
            import subprocess

            cmd = [
                sys.executable,
                "-m",
                "mcp",
                "dev",
                str(Path(__file__).parent / "src" / "slack_notifier_mcp" / "server.py"),
            ]
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n👋 Server stopped by user")
        except Exception as e:
            print(f"❌ Failed to start development server: {e}")
            sys.exit(1)
    else:
        print("🚀 Starting Slack Notifier MCP Server...")
        print("   Server will communicate via stdio transport")
        print("   Press Ctrl+C to stop")
        print()

        try:
            from slack_notifier_mcp.server import main

            main()
        except KeyboardInterrupt:
            print("\n👋 Server stopped by user")
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            sys.exit(1)


def show_help():
    """Show detailed help information."""
    print(__doc__)
    print("Environment Variables:")
    print("  SLACK_BOT_TOKEN     Required. Your Slack bot token (starts with xoxb-)")
    print("  SLACK_CHANNEL       Required. Channel name (general) or ID (C1234567890)")
    print("  PYTHONPATH          Optional. Additional Python paths")
    print()
    print("Examples:")
    print("  python run.py                    # Start server in production mode")
    print("  python run.py --dev              # Start with MCP Inspector")
    print("  python run.py --env-file .env.prod  # Use custom .env file")
    print()
    print("For more information, see README.md")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run the Slack Notifier MCP Server", add_help=False
    )
    parser.add_argument(
        "--dev", action="store_true", help="Run in development mode with MCP Inspector"
    )
    parser.add_argument(
        "--env-file", default=".env", help="Path to .env file (default: .env)"
    )
    parser.add_argument("--help", action="store_true", help="Show help message")

    args = parser.parse_args()

    if args.help:
        show_help()
        return

    print("🔧 Slack Notifier MCP Server")
    print("=" * 40)

    # Try to load environment file
    if load_env_file(args.env_file):
        print(f"✅ Loaded environment from {args.env_file}")
    else:
        if args.env_file != ".env" or Path(".env").exists():
            print(f"⚠️  Could not load {args.env_file}")
        print("📋 Using system environment variables")

    # Validate configuration
    if not validate_configuration():
        print("💡 Tip: Copy .env.example to .env and fill in your bot token")
        sys.exit(1)

    bot_token = os.getenv("SLACK_BOT_TOKEN", "")
    channel = os.getenv("SLACK_CHANNEL", "")
    print(f"✅ Configuration valid (token: {bot_token[:20]}..., channel: {channel})")
    print()

    # Run the server
    run_server(dev_mode=args.dev)


if __name__ == "__main__":
    main()
