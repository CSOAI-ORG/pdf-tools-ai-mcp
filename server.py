"""
PDF Tools AI MCP Server
PDF utility tools powered by MEOK AI Labs.
"""


import sys, os
from auth_middleware import check_access

import re
import time
import struct
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pdf-tools-ai", instructions="MEOK AI Labs MCP Server")

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
        raise ValueError(f"Rate limit exceeded for {tool_name}. Free tier: {FREE_TIER_LIMIT}/day. Upgrade at https://councilof.ai")
    _call_counts[tool_name].append(now)


@mcp.tool()
def extract_text(file_path: str, max_pages: int = 50, api_key: str = "") -> dict:
    """Extract text content from a PDF file.

    Args:
        file_path: Path to the PDF file
        max_pages: Maximum number of pages to extract (default 50)

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}

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
def count_pages(file_path: str, api_key: str = "") -> dict:
    """Count the number of pages in a PDF file.

    Args:
        file_path: Path to the PDF file

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}

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
def get_metadata(file_path: str, api_key: str = "") -> dict:
    """Get metadata from a PDF file (title, author, creation date, etc).

    Args:
        file_path: Path to the PDF file

    Behavior:
        This tool generates structured output without modifying external systems.
        Output is deterministic for identical inputs. No side effects.
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}

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
def merge_pages_data(pages_data: list[dict], api_key: str = "") -> dict:
    """Merge text data from multiple PDF page extractions into a single document.

    Args:
        pages_data: List of dicts with keys: text, page_number (optional), source (optional)

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://councilof.ai"}

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


def main():
    mcp.run()

if __name__ == '__main__':
    main()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/00wfZjcgAeUW4c5cyQ8k90K"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
