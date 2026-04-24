# Setup with an AI agent

Paste this prompt to your agent (Claude / Codex / Gemini CLI / OpenCode):

> Install `imagine-mcp` MCP server and configure it.
>
> 1. Add to MCP client config:
>    ```json
>    { "mcpServers": { "imagine": { "command": "uvx", "args": ["imagine-mcp"] } } }
>    ```
> 2. Restart the client.
> 3. Call `config(action="open_relay")` on the `imagine` server.
> 4. Open the URL shown, paste my API keys (Google AI Studio, OpenAI, xAI -- any subset), and submit.
> 5. Confirm with `config(action="status")`.

The agent handles everything. You provide only API keys via browser.
