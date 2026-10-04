# Guide: Model Context Protocol (MCP) Setup

`google-news-api` ships with a production Model Context Protocol (MCP) server
enabling LLMs (such as Claude Desktop, Cursor, and custom agent platforms) to
search and decode news articles.

## Installation

Install the MCP extras:

```bash
pip install "google-news-api[mcp]"
```

## Running the Server

### 1. Stdio Mode (Default for Local Assistants)

```bash
# Starts MCP server on stdin/stdout
google-news-mcp
```

### 2. HTTP Transport (Streamable Web Deployment)

```bash
# Starts MCP HTTP server on port 8000
google-news-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

## Claude Desktop Configuration

Add the server to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-news": {
      "command": "google-news-mcp",
      "args": []
    }
  }
}
```

## Exposed MCP Tools

The server registers 5 standard tools:

1. **`news_search`**: Search articles by query with optional date filters and URL decoding.
2. **`batch_news_search`**: Run multiple search queries concurrently with rate limiting.
3. **`top_news`**: Retrieve top news for standard topics (`WORLD`, `NATION`, `BUSINESS`, `TECHNOLOGY`, `ENTERTAINMENT`, `SPORTS`, `SCIENCE`, `HEALTH`).
4. **`location_news`**: Fetch local headlines for a specific city or region (e.g. `"Berlin"`, `"San Francisco"`).
5. **`server_info`**: Inspect server status, uptime, and configuration.
