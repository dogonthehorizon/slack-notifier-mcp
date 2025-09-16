# Slack Notifier MCP Server

> [!WARNING]
> This is preview software and is not intended for production use. Use at your own risk.

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides a tool for sending progress update notifications to a pre-configured Slack channel using OAuth bot tokens. This server is designed to help AI agents communicate their task completion status and progress updates to a designated team channel via the Slack Web API.

## Features

- **Single Tool**: `slack-progress-update` - Send formatted progress notifications to a pre-configured Slack channel
- **OAuth Bot Token Authentication**: Secure authentication using Slack bot tokens with proper scopes
- **Rich Formatting**: Uses Slack's Block Kit for well-formatted messages with emojis and structured content
- **Static Channel Configuration**: Messages sent to a single channel configured via environment variable
- **Thread Support**: Optional thread replies for organized conversations
- **Multiple Status Types**: Support for completed, failed, in_progress, warning, info, success, error, and running statuses
- **Environment-based Configuration**: Secure bot token configuration via environment variables
- **Stdio Transport**: Runs locally using stdio transport for easy integration
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Connection Testing**: Built-in connection validation on startup

## Installation

### Prerequisites

- Python 3.10 or higher
- A Slack workspace with app creation permissions
- UV package manager (recommended) or pip

### Install Dependencies

Using UV (recommended):

```bash
cd slack-notifier-mcp
uv sync
```

Using pip:

```bash
cd slack-notifier-mcp
pip install -e .
```

## Configuration

### 1. Create a Slack App and Get Bot Token

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Enter an app name (e.g., "Agent Progress Notifier") and select your workspace
4. In the sidebar, go to "OAuth & Permissions"
5. Under "Bot Token Scopes", add these scopes:
   - `chat:write` (required) - Send messages as the bot
   - `chat:write.public` (optional) - Post to channels without joining them first
6. Click "Install to Workspace" and authorize the app
7. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 2. Add Bot to Channels

For the bot to send messages to channels, it needs to be added:

1. Go to the Slack channel where you want notifications
2. Type `/invite @YourBotName` or use the channel settings to add the bot
3. Alternatively, use the `chat:write.public` scope to post without joining

### 3. Set Environment Variables

Set the required environment variables:

```bash
export SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
export SLACK_CHANNEL="general"  # or your preferred channel name/ID
```

Or create a `.env` file:

```bash
echo "SLACK_BOT_TOKEN=xoxb-your-bot-token-here" >> .env
echo "SLACK_CHANNEL=general" >> .env
```

## Usage

### Running the Server

Start the MCP server using stdio transport:

```bash
# Using UV
uv run slack-notifier-mcp

# Or using the module directly
python -m slack_notifier_mcp.server

# Or using the convenient run script
python run.py                  # Production mode
python run.py --dev            # Development mode with MCP Inspector
```

### Using with MCP Clients

Once the server is running, MCP clients can connect to it and use the `slack-progress-update` tool.

#### Tool: `slack-progress-update`

Sends a progress update notification to the pre-configured Slack channel.

**Parameters:**

- `summary` (required): Brief summary of what was accomplished
- `details` (optional): Detailed information about the task
- `status` (optional): Status of the task - one of:
  - `completed` (default) - ✅
  - `failed` - ❌
  - `in_progress` - 🔄
  - `warning` - ⚠️
  - `info` - ℹ️
  - `success` - ✅
  - `error` - ❌
  - `running` - 🔄
- `timestamp` (optional): ISO timestamp string (defaults to current time)
- `task_id` (optional): Task identifier for tracking
- `agent_name` (optional): Name of the agent performing the task
- `thread_ts` (optional): Thread timestamp to reply in a thread

**Example Usage:**

```python
# Basic usage
result = client.call_tool("slack-progress-update", {
    "summary": "Successfully processed 150 customer records",
    "status": "completed"
})

# Detailed usage with all parameters
result = client.call_tool("slack-progress-update", {
    "summary": "Data analysis pipeline completed",
    "details": "Processed 1,250 rows, identified 23 anomalies, generated 5 reports",
    "status": "completed",
    "task_id": "TASK-2024-001",
    "agent_name": "DataAnalysisAgent",
    "timestamp": "2024-01-15T10:30:00Z"
})

# Error notification with thread reply
result = client.call_tool("slack-progress-update", {
    "summary": "Failed to connect to external API",
    "details": "Connection timeout after 30 seconds. Will retry in 5 minutes.",
    "status": "failed",
    "agent_name": "APIConnectorAgent",
    "thread_ts": "1642251234.123456"  # Reply in existing thread
})
```

### Example Slack Message Output

The tool generates rich, formatted messages in Slack that look like this:

```
Agent Progress Update
═══════════════════════════════════════

Agent: DataAnalysisAgent              Task ID: TASK-2024-001
Status: ✅ Completed                  Timestamp: 2024-01-15 10:30:00 UTC

Summary:
Data analysis pipeline completed

Details:
Processed 1,250 rows, identified 23 anomalies, generated 5 reports
```

## Integration with Zed Editor

[Zed](https://zed.dev) is a modern code editor with built-in AI capabilities that supports MCP servers. You can integrate this Slack Notifier MCP server with Zed to send progress updates directly from your AI assistant sessions.

### Prerequisites: Installing uvx

The recommended way to run this MCP server with Zed is using `uvx`, which allows you to run Python applications in isolated environments without manual installation.

**Install UV (which includes uvx):**

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.sh | iex"

# Or using pip
pip install uv
```

**Verify installation:**

```bash
uvx --version
```

**Why uvx?**

- ✅ **Automatic dependency management**: uvx handles all Python dependencies automatically
- ✅ **Isolated environments**: No conflicts with your system Python or other projects
- ✅ **Simple configuration**: Just specify the package name, no paths needed
- ✅ **Always up-to-date**: Can automatically use the latest published version

**Testing uvx with the package:**

Before configuring Zed, test that uvx can run the package:

```bash
# Test that uvx can find and run the package
SLACK_BOT_TOKEN="test" SLACK_CHANNEL="test" uvx slack-notifier-mcp --help

# If the package isn't published yet, you can install from the local directory
uvx --from /path/to/slack-notifier-mcp slack-notifier-mcp --help
```

**Note**: If you're using an unpublished local version, you'll need to use the local development configuration in Zed (see Alternative configuration below).

### Setting Up in Zed

Zed supports MCP servers through custom server configuration in your `settings.json` file. Here's how to set it up:

#### 1. Configure the MCP Server (Recommended: uvx)

Add the following configuration to your Zed `settings.json` file (accessible via `Cmd/Ctrl + ,` or the Command Palette → `zed: open settings`):

```json
{
  "context_servers": {
    "slack-notifier": {
      "source": "custom",
      "command": "uvx",
      "args": ["slack-notifier-mcp"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-bot-token-here",
        "SLACK_CHANNEL": "general"
      }
    }
  }
}
```

This configuration:

- Uses `uvx` to automatically handle dependencies
- Runs the published `slack-notifier-mcp` package
- Sets required environment variables for Slack integration

#### 2. Alternative: Local Development

If you're working with a local development version:

```json
{
  "context_servers": {
    "slack-notifier": {
      "source": "custom",
      "command": "python",
      "args": ["/path/to/slack-notifier-mcp/run.py"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-bot-token-here",
        "SLACK_CHANNEL": "general"
      }
    }
  }
}
```

#### 3. Verify Installation

1. Open Zed and access the Agent Panel (`Cmd/Ctrl + Shift + A`)
2. Go to the Agent Panel settings (gear icon in top-right)
3. Look for "slack-notifier" in the server list
4. Check that the indicator dot is green, meaning "Server is active"

#### 4. Using the Tool

Once configured, you can use the Slack notification tool in your AI conversations:

- Mention the server by name: "Use the slack-notifier to send a progress update"
- The AI assistant will use the `slack-progress-update` tool to send formatted messages to your configured Slack channel

#### 5. Tool Approval Settings

By default, Zed may require approval for tool actions. To configure this:

```json
{
  "agent": {
    "always_allow_tool_actions": true
  }
}
```

Set to `false` if you want to manually approve each tool call.

#### 6. Custom Profile (Optional)

For dedicated Slack notification workflows, you can create a custom profile that focuses on the Slack tools:

```json
{
  "agent": {
    "profiles": {
      "slack-notifications": {
        "name": "Slack Notifications",
        "tools": {
          "thinking": true,
          "fetch": false,
          "terminal": false,
          "edit_file": false
        },
        "enable_all_context_servers": false,
        "context_servers": {
          "slack-notifier": {
            "tools": {
              "slack-progress-update": true
            }
          }
        }
      }
    }
  }
}
```

### Zed Troubleshooting

If you encounter issues with the Slack Notifier MCP server in Zed, try these solutions:

#### Server Not Active (Red/Yellow Indicator)

1. **Check uvx installation**: Ensure `uvx` is installed and available in your system PATH (`uvx --version`)
2. **Verify environment variables**: Make sure `SLACK_BOT_TOKEN` and `SLACK_CHANNEL` are properly set in the `env` section
3. **Test uvx manually**: Try running `uvx slack-notifier-mcp` in your terminal to see if it works
4. **Check package availability**: Ensure the `slack-notifier-mcp` package can be found by uvx
5. **Review Zed logs**: Open the Command Palette and run `zed: open log file` to see detailed error messages

#### Tool Not Being Used by AI Assistant

1. **Mention the server explicitly**: Say "Use the slack-notifier to send an update" in your prompts
2. **Check tool approval settings**: Ensure `always_allow_tool_actions` is set appropriately
3. **Verify server is active**: The indicator dot should be green in Agent Panel settings
4. **Try a custom profile**: Create a dedicated profile that only enables the Slack notification tool

#### Configuration Issues

**Command Problems:**

```json
// ❌ Wrong - using python directly
"command": "python",
"args": ["/some/path/run.py"]

// ✅ Correct - using uvx (recommended)
"command": "uvx",
"args": ["slack-notifier-mcp"]

// ✅ Alternative - local development
"command": "python",
"args": ["/absolute/path/to/slack-notifier-mcp/run.py"]
```

**Package Name Issues:**

```json
// ❌ Wrong - incorrect package name
"args": ["slack-notifier"]

// ✅ Correct - exact package name
"args": ["slack-notifier-mcp"]
```

**Environment Variable Problems:**

```json
// ❌ Wrong - missing required variables
"env": {
  "SLACK_BOT_TOKEN": "xoxb-token"
  // Missing SLACK_CHANNEL
}

// ✅ Correct - both variables set
"env": {
  "SLACK_BOT_TOKEN": "xoxb-your-token",
  "SLACK_CHANNEL": "general"
}
```

#### Testing the Integration

You can test if everything is working by asking the AI assistant:

> "Please use the slack-notifier to send a test progress update saying 'Zed integration test completed' with status 'success'"

The assistant should use the `slack-progress-update` tool and you should see the message appear in your configured Slack channel.

#### Manual Testing

You can also test the uvx command directly:

```bash
# Set your environment variables
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_CHANNEL="general"

# Test the command that Zed will run
uvx slack-notifier-mcp

# The server should start and show connection confirmation
# Press Ctrl+C to stop
```

If this works in your terminal, it should work in Zed as well.

## Development

### Running in Development Mode

For development and testing, you can use the MCP development server:

```bash
uv run mcp dev src/slack_notifier_mcp/server.py
```

This will start the server with the MCP Inspector for easy testing.

### Project Structure

```
slack-notifier-mcp/
├── src/
│   └── slack_notifier_mcp/
│       ├── __init__.py
│       └── server.py          # Main server implementation
├── pyproject.toml             # Project configuration
├── run.py                     # Convenient run script
├── README.md                  # This file
├── .env.example              # Environment template
├── LICENSE                   # MIT license
└── .gitignore
```

## Troubleshooting

### Common Issues

1. **"Slack bot token not configured" error**
   - Make sure the `SLACK_BOT_TOKEN` environment variable is set
   - Verify the bot token starts with `xoxb-`
   - Check that the token hasn't been regenerated in your Slack app settings

2. **"Slack channel not configured" error**
   - Make sure the `SLACK_CHANNEL` environment variable is set
   - Use the channel name (without #) or channel ID

3. **"Channel not found" error**
   - Verify the configured channel name or ID is correct
   - Make sure the bot has been added to the channel
   - For private channels, the bot must be explicitly invited

4. **"Not in channel" error**
   - Add the bot to the configured channel: `/invite @YourBotName`
   - Or add the `chat:write.public` scope to post without joining

5. **"Missing scope" error**
   - Go to your Slack app's "OAuth & Permissions" page
   - Add the `chat:write` scope under "Bot Token Scopes"
   - Reinstall the app to your workspace

6. **"Invalid auth" error**
   - Your bot token may be expired or invalid
   - Regenerate the token in your Slack app settings
   - Update the `SLACK_BOT_TOKEN` environment variable

### Debug Mode

Enable debug logging by setting the log level:

```bash
export PYTHONPATH=src
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from slack_notifier_mcp.server import main
main()
"
```

### Testing Connection

The server automatically tests the Slack connection on startup. You'll see a message like:

```
✅ Connected to Slack as: your-bot-name on team Your Team Name
```

## Channel Configuration

The server sends messages to a single channel configured via the `SLACK_CHANNEL` environment variable.

Supported channel formats:

- **Channel name**: `general` (without # prefix)
- **Channel ID**: `C1234567890` (recommended for reliability)
- **Private channels**: Use channel ID, and bot must be invited

To find a channel ID:

1. Right-click on the channel in Slack
2. Select "Copy link"
3. The channel ID is the part after `/archives/` in the URL

## Security Considerations

- **Bot Token**: Keep your Slack bot token secure and never commit it to version control
- **Environment Variables**: Use environment variables or secure secret management for bot tokens
- **Scopes**: Only grant necessary OAuth scopes to your bot
- **Network**: The server makes outbound HTTPS requests to Slack's API

## Required Slack Scopes

Your Slack bot needs these OAuth scopes:

- `chat:write` (required) - Send messages as the bot
- `chat:write.public` (optional) - Post to public channels without joining

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.
