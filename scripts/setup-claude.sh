#!/bin/sh
# Sets up Claude Code MCP servers and settings for web development

# Playwright MCP server (project-level)
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
EOF

# Claude local settings with permissions
mkdir -p .claude
cat > .claude/settings.local.json << 'EOF'
{
  "permissions": {
    "allow": ["mcp__playwright"],
    "deny": []
  }
}
EOF

echo "Done — .mcp.json and .claude/settings.local.json created."
echo "Playwright MCP will be available next time you start Claude Code."
