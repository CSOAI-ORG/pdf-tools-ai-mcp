"""
PDF Tools AI MCP Server
PDF utility tools powered by MEOK AI Labs.
"""

import re
import time
import struct
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pdf-tools-ai-mcp")

_call_counts: dict[str, list[float]] = defaultdict(list)
FREE_TIER_LIMIT = 50
WINDOW = 86400

# Path traversal protection
BLOCKED_PATH_PATTERNS = ["/etc/", "/var/", "/proc/", "/sys/", "/dev/", ".."]


def _validate_file_path(file_path: str) -> str | None:
    """Validate file path against traversal attacks. Returns error message or None."""
    import os
    real = os.path.realpath(file_path)
    for pattern in BLOCKED_PATH_PATTERNS:
        if pattern in file_path:
            return f"Access denied: path contains blocked pattern '{pattern}'"
    if not os.path.isfile(real):
        return f"File not found: {file_path}"
    return None

def _check_rate_limit(tool_name: str) -> None:
    now = time.time()
    _call_counts[tool_name] = [t for t in _call_counts[tool_name] if now - t < WINDOW]
    if len(_call_counts[tool_name]) >= FREE_TIER_LIMIT:
        raise ValueError(f"Rate limit exceeded for {tool_name}. Free tier: {FREE_TIER_LIMIT}/day. Upgrade at https://meok.ai/pricing")
    _call_counts[tool_name].append(now)


@mcp.tool()
def extract_text(file_path: str, max_pages: int = 50) -> dict:
    """Extract text content from a PDF file.

    Args:
        file_path: Path to the PDF file
        max_pages: Maximum number of pages to extract (default 50)
    """
    _check_rate_limit("extract_text")
    path_err = _validate_file_path(file_path)
    if path_err:
        return {"error": path_err}
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            pages = []
            for i, page in enumerate(reader.pages[:max_pages]):
                text = page.extract_text() or ""
                pages.append({"page": i + 1, "text": text[:5000]})
            return {"file": file_path, "pages": pages, "page_count": len(reader.pages), "extracted": len(pages)}
    except ImportError:
        # Fallback: basic text extraction
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            if not data.startswith(b'%PDF'):
                return {"error": "Not a valid PDF file"}
            texts = re.findall(rb'\(([^)]+)\)', data)
            text = b' '.join(texts[:500]).decode('latin-1', errors='replace')
            return {"file": file_path, "text": text[:10000], "note": "Basic extraction. Install PyPDF2 for better results."}
        except Exception as e:
            return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def count_pages(file_path: str) -> dict:
    """Count the number of pages in a PDF file.

    Args:
        file_path: Path to the PDF file
    """
    _check_rate_limit("count_pages")
    path_err = _validate_file_path(file_path)
    if path_err:
        return {"error": path_err}
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        if not data.startswith(b'%PDF'):
            return {"error": "Not a valid PDF file"}
        try:
            import PyPDF2
            from io import BytesIO
            reader = PyPDF2.PdfReader(BytesIO(data))
            return {"file": file_path, "pages": len(reader.pages), "method": "PyPDF2"}
        except ImportError:
            count = len(re.findall(rb'/Type\s*/Page[^s]', data))
            return {"file": file_path, "pages": count, "method": "regex", "note": "Approximate. Install PyPDF2 for accuracy."}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_metadata(file_path: str) -> dict:
    """Get metadata from a PDF file (title, author, creation date, etc).

    Args:
        file_path: Path to the PDF file
    """
    _check_rate_limit("get_metadata")
    path_err = _validate_file_path(file_path)
    if path_err:
        return {"error": path_err}
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        if not data.startswith(b'%PDF'):
            return {"error": "Not a valid PDF file"}
        version = data[:8].decode('latin-1').strip()
        try:
            import PyPDF2
            from io import BytesIO
            reader = PyPDF2.PdfReader(BytesIO(data))
            meta = reader.metadata or {}
            info = {k.lstrip('/'): str(v)[:200] for k, v in meta.items() if v}
            info["pages"] = len(reader.pages)
            info["pdf_version"] = version
            info["file_size_bytes"] = len(data)
            return {"file": file_path, "metadata": info}
        except ImportError:
            info = {"pdf_version": version, "file_size_bytes": len(data)}
            for field in [b'/Title', b'/Author', b'/Subject', b'/Creator', b'/Producer']:
                match = re.search(field + rb'\s*\(([^)]*)\)', data)
                if match:
                    info[field.decode().lstrip('/')] = match.group(1).decode('latin-1', errors='replace')
            return {"file": file_path, "metadata": info, "note": "Install PyPDF2 for complete metadata."}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def merge_pages_data(pages_data: list[dict]) -> dict:
    """Merge text data from multiple PDF page extractions into a single document.

    Args:
        pages_data: List of dicts with keys: text, page_number (optional), source (optional)
    """
    _check_rate_limit("merge_pages_data")
    if not pages_data:
        return {"error": "No pages data provided"}
    merged_text = []
    total_chars = 0
    sources = set()
    for i, page in enumerate(pages_data):
        text = page.get("text", "")
        page_num = page.get("page_number", i + 1)
        source = page.get("source", "unknown")
        sources.add(source)
        merged_text.append(f"--- Page {page_num} ({source}) ---\n{text}")
        total_chars += len(text)
    return {
        "merged_text": "\n\n".join(merged_text),
        "total_pages": len(pages_data),
        "total_characters": total_chars,
        "sources": list(sources),
        "word_count_estimate": total_chars // 5,
    }


if __name__ == "__main__":
    mcp.run()
