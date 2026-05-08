<div align="center">

# Pdf Tools Ai MCP

**PDF Tools AI MCP Server**

[![PyPI](https://img.shields.io/pypi/v/meok-pdf-tools-ai-mcp)](https://pypi.org/project/meok-pdf-tools-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

PDF Tools AI MCP Server
PDF utility tools powered by MEOK AI Labs.

## Tools

| Tool | Description |
|------|-------------|
| `extract_text` | Extract text content from a PDF file. |
| `count_pages` | Count the number of pages in a PDF file. |
| `get_metadata` | Get metadata from a PDF file (title, author, creation date, etc). |
| `merge_pages_data` | Merge text data from multiple PDF page extractions into a single document. |

## Installation

```bash
pip install meok-pdf-tools-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pdf-tools-ai": {
      "command": "python",
      "args": ["-m", "meok_pdf_tools_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 4 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
