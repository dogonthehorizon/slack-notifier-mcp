"""
Main MCP server implementation for Slack notifications using OAuth tokens.

This module provides a Model Context Protocol server that exposes a single tool
for sending progress update notifications to a pre-configured Slack channel
using the Slack Web API with OAuth bot tokens.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SLACK_BOT_TOKEN_ENV = "SLACK_BOT_TOKEN"
SLACK_CHANNEL_ENV = "SLACK_CHANNEL"

# Create the MCP server
mcp = FastMCP("Slack Notifier")


def get_slack_client() -> WebClient:
    """
    Get a configured Slack WebClient using OAuth bot token.

    Returns:
        Configured Slack WebClient

    Raises:
        ValueError: If the bot token is not configured
    """
    bot_token = os.getenv(SLACK_BOT_TOKEN_ENV)
    if not bot_token:
        raise ValueError(
            f"Slack bot token not configured. Please set the {SLACK_BOT_TOKEN_ENV} environment variable."
        )

    if not bot_token.startswith(("xoxb-", "xoxp-")):
        raise ValueError(
            "Invalid Slack bot token format. Token should start with 'xoxb-' for bot tokens or 'xoxp-' for user tokens."
        )

    return WebClient(token=bot_token)


def get_slack_channel() -> str:
    """
    Get the configured Slack channel from environment variables.

    Returns:
        Configured Slack channel

    Raises:
        ValueError: If the channel is not configured
    """
    channel = os.getenv(SLACK_CHANNEL_ENV)
    if not channel:
        raise ValueError(
            f"Slack channel not configured. Please set the {SLACK_CHANNEL_ENV} environment variable."
        )

    # Remove # prefix if present
    if channel.startswith("#"):
        channel = channel[1:]

    return channel


def format_slack_blocks(
    summary: str,
    details: Optional[str] = None,
    status: str = "completed",
    timestamp: Optional[str] = None,
    task_id: Optional[str] = None,
    agent_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Format a progress update message using Slack Block Kit.

    Args:
        summary: Brief summary of what was accomplished
        details: Optional detailed information about the task
        status: Status of the task (completed, failed, in_progress, etc.)
        timestamp: Optional ISO timestamp string
        task_id: Optional task identifier
        agent_name: Optional name of the agent

    Returns:
        List of Slack Block Kit blocks
    """
    # Status emoji mapping
    status_emojis = {
        "completed": "✅",
        "failed": "❌",
        "in_progress": "🔄",
        "warning": "⚠️",
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "running": "🔄",
    }

    emoji = status_emojis.get(status.lower(), "📋")

    # Format timestamp
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except ValueError:
            formatted_time = timestamp
    else:
        formatted_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Agent Progress Update"},
        }
    ]

    # Build main content section
    main_fields = []

    if agent_name:
        main_fields.append({"type": "mrkdwn", "text": f"*Agent:*\n{agent_name}"})

    if task_id:
        main_fields.append({"type": "mrkdwn", "text": f"*Task ID:*\n`{task_id}`"})

    main_fields.extend(
        [
            {"type": "mrkdwn", "text": f"*Status:*\n{emoji} {status.title()}"},
            {"type": "mrkdwn", "text": f"*Timestamp:*\n{formatted_time}"},
        ]
    )

    blocks.append({"type": "section", "fields": main_fields})

    # Add summary section
    blocks.append(
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Summary:*\n{summary}"},
        }
    )

    # Add details section if provided
    if details:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Details:*\n{details}"},
            }
        )

    return blocks


@mcp.tool()
def slack_progress_update(
    summary: str,
    details: Optional[str] = None,
    status: str = "completed",
    timestamp: Optional[str] = None,
    task_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    thread_ts: Optional[str] = None,
) -> str:
    """
    Send a progress update notification to the pre-configured Slack channel.

    This tool sends a formatted message to the configured Slack channel summarizing what
    an agent has accomplished when it finishes its current task. The message includes
    status, summary, optional details, and timestamp information.

    Args:
        summary: Brief summary of what was accomplished (required)
        details: Optional detailed information about the task
        status: Status of the task (completed, failed, in_progress, warning, info, success, error, running)
        timestamp: Optional ISO timestamp string (defaults to current time)
        task_id: Optional task identifier for tracking
        agent_name: Optional name of the agent performing the task
        thread_ts: Optional thread timestamp to reply in a thread

    Returns:
        Success message confirming the notification was sent

    Raises:
        Exception: If the Slack bot token/channel is not configured or message sending fails
    """
    try:
        # Get Slack client and channel
        client = get_slack_client()
        channel = get_slack_channel()

        # Format the message blocks
        blocks = format_slack_blocks(
            summary=summary,
            details=details,
            status=status,
            timestamp=timestamp,
            task_id=task_id,
            agent_name=agent_name,
        )

        # Create fallback text for notifications
        fallback_text = f"Agent Progress Update: {summary} (Status: {status})"

        # Prepare message payload
        message_kwargs = {
            "channel": channel,
            "text": fallback_text,
            "blocks": blocks,
        }

        # Add thread_ts if provided
        if thread_ts:
            message_kwargs["thread_ts"] = thread_ts

        # Send the message
        response = client.chat_postMessage(**message_kwargs)

        if response["ok"]:
            message_ts = response["ts"]
            channel_info = response.get("channel", channel)

            logger.info(
                f"Successfully sent Slack notification to {channel_info}: {summary}"
            )

            result_msg = (
                f"✅ Progress update sent to Slack successfully!\n"
                f"Channel: {channel}\n"
                f"Status: {status}\n"
                f"Summary: {summary}\n"
                f"Message timestamp: {message_ts}"
            )

            if thread_ts:
                result_msg += f"\nThread: {thread_ts}"

            return result_msg
        else:
            error_msg = f"Failed to send Slack notification. Response: {response}"
            logger.error(error_msg)
            raise Exception(error_msg)

    except ValueError as e:
        # Configuration or validation error
        error_msg = f"Configuration error: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    except SlackApiError as e:
        # Slack API error
        error_details = e.response.get("error", "unknown_error")
        error_msg = f"Slack API error: {error_details}"

        # Provide helpful error messages for common issues
        if error_details == "channel_not_found":
            try:
                channel = get_slack_channel()
                error_msg += f" - Channel '{channel}' not found. Make sure the channel exists and the bot is added to it."
            except ValueError:
                error_msg += (
                    " - Channel not found. Check your SLACK_CHANNEL configuration."
                )
        elif error_details == "not_in_channel":
            try:
                channel = get_slack_channel()
                error_msg += f" - Bot is not a member of channel '{channel}'. Please add the bot to the channel."
            except ValueError:
                error_msg += " - Bot is not a member of the configured channel."
        elif error_details == "invalid_auth":
            error_msg += " - Invalid bot token. Please check your SLACK_BOT_TOKEN."
        elif error_details == "missing_scope":
            error_msg += " - Bot token missing required scopes. Ensure 'chat:write' scope is enabled."

        logger.error(error_msg)
        raise Exception(error_msg)

    except Exception as e:
        # Generic error
        error_msg = f"Unexpected error sending Slack notification: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def test_slack_connection() -> Dict[str, Any]:
    """
    Test the Slack connection and return bot information.

    Returns:
        Dictionary containing bot information and connection status

    Raises:
        Exception: If connection test fails
    """
    try:
        client = get_slack_client()
        channel = get_slack_channel()

        # Test API connection
        auth_response = client.auth_test()

        if auth_response["ok"]:
            return {
                "status": "connected",
                "bot_user_id": auth_response.get("user_id"),
                "bot_user": auth_response.get("user"),
                "team": auth_response.get("team"),
                "team_id": auth_response.get("team_id"),
                "url": auth_response.get("url"),
                "channel": channel,
            }
        else:
            raise Exception(f"Auth test failed: {auth_response}")

    except Exception as e:
        raise Exception(f"Connection test failed: {str(e)}")


def main():
    """
    Main entry point for the Slack Notifier MCP server.

    This function starts the MCP server using stdio transport, making it available
    for communication with MCP clients.
    """
    try:
        # Validate configuration on startup
        get_slack_client()  # Validate bot token
        channel = get_slack_channel()  # Validate channel
        logger.info("Slack Notifier MCP server starting...")

        # Test connection
        connection_info = test_slack_connection()
        logger.info(
            f"✅ Connected to Slack as: {connection_info['bot_user']} on team {connection_info['team']}"
        )
        logger.info(f"✅ Configured to send notifications to channel: {channel}")

        # Run the server with stdio transport (default)
        mcp.run(transport="stdio")

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error(
            f"Please set the {SLACK_BOT_TOKEN_ENV} and {SLACK_CHANNEL_ENV} environment variables."
        )
        logger.error("Bot token should start with 'xoxb-' and have 'chat:write' scope.")
        logger.error("Channel can be a name (general) or ID (C1234567890).")
        exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        exit(1)


if __name__ == "__main__":
    main()
