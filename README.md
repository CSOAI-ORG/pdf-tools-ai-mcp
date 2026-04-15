# Pdf Tools Ai

> By [MEOK AI Labs](https://meok.ai) — MEOK AI Labs MCP Server

PDF Tools AI MCP Server

## Installation

```bash
pip install pdf-tools-ai-mcp
```

## Usage

```bash
# Run standalone
python server.py

# Or via MCP
mcp install pdf-tools-ai-mcp
```

## Tools

### `extract_text`
Extract text content from a PDF file.

**Parameters:**
- `file_path` (str)
- `max_pages` (int)

### `count_pages`
Count the number of pages in a PDF file.

**Parameters:**
- `file_path` (str)

### `get_metadata`
Get metadata from a PDF file (title, author, creation date, etc).

**Parameters:**
- `file_path` (str)

### `merge_pages_data`
Merge text data from multiple PDF page extractions into a single document.

**Parameters:**
- `pages_data` (str)


## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## Links

- **Website**: [meok.ai](https://meok.ai)
- **GitHub**: [CSOAI-ORG/pdf-tools-ai-mcp](https://github.com/CSOAI-ORG/pdf-tools-ai-mcp)
- **PyPI**: [pypi.org/project/pdf-tools-ai-mcp](https://pypi.org/project/pdf-tools-ai-mcp/)

## License

MIT — MEOK AI Labs
