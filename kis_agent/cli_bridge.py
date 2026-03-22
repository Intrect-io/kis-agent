#!/usr/bin/env python3
"""kis-agent JSON subprocess bridge.

This module implements a JSON-based bridge protocol for subprocess communication
with TypeScript CLI clients. It reads BridgeRequest from stdin and writes
BridgeResponse to stdout, one JSON object per line.

Protocol:
- Input: BridgeRequest JSON via stdin
- Output: BridgeResponse JSON via stdout
- Format: JSON lines (one complete JSON object per line)

Typical usage:
  python -m kis_agent.cli_bridge < request.json > response.json

Or as subprocess in TypeScript:
  const proc = spawn('python', ['-m', 'kis_agent.cli_bridge'])
  proc.stdin.write(JSON.stringify(request))
  proc.stdout.on('data', (data) => { ... })
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from kis_agent.cli.main import (
    _check_market_status,
    _create_agent,
    _market_status,
    cmd_balance,
    cmd_futures,
    cmd_orderbook,
    cmd_overseas,
    cmd_price,
    cmd_query,
    cmd_schema,
)


class BridgeResponse:
    """Helper to construct BridgeResponse objects."""

    @staticmethod
    def success(data: Any, notice: Optional[str] = None) -> str:
        """Create success response JSON."""
        response = {"data": data}
        if notice:
            response["_notice"] = notice
        return json.dumps(response, ensure_ascii=False, default=str)

    @staticmethod
    def error(message: str, code: str = "Error", traceback: Optional[str] = None) -> str:
        """Create error response JSON."""
        response = {"error": message, "code": code}
        if traceback:
            response["traceback"] = traceback
        return json.dumps(response, ensure_ascii=False, default=str)


class SimpleNamespace:
    """Simple object for storing request args as attributes."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _parse_request(line: str) -> Dict[str, Any]:
    """Parse BridgeRequest JSON line."""
    try:
        request = json.loads(line)
        if not isinstance(request, dict):
            raise ValueError("Request must be a JSON object")
        if "method" not in request:
            raise ValueError("Request missing required 'method' field")
        if "args" not in request:
            raise ValueError("Request missing required 'args' field")
        return request
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e


def _execute_command(method: str, args: Dict[str, Any], kwargs: Dict[str, Any]) -> Any:
    """Execute CLI command handler with given args."""
    # Convert args dict to namespace object for argparse compatibility
    ns = SimpleNamespace(**args, **kwargs)

    # Map handler functions
    handlers = {
        "price": cmd_price,
        "balance": cmd_balance,
        "orderbook": cmd_orderbook,
        "overseas": cmd_overseas,
        "futures": cmd_futures,
        "query": cmd_query,
        "schema": cmd_schema,
    }

    handler = handlers.get(method)
    if not handler:
        raise ValueError(f"Unknown command: {method}. Available: {', '.join(handlers.keys())}")

    # Create temporary output capture
    import io

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        handler(ns)
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        # Parse captured JSON output
        if output:
            return json.loads(output.strip())
        return {"data": None}
    finally:
        sys.stdout = old_stdout


def main():
    """Main bridge loop — read BridgeRequest from stdin, write BridgeResponse to stdout."""
    try:
        # Pre-create agent and check market status once
        _create_agent()
    except Exception as e:
        print(BridgeResponse.error(f"Failed to initialize: {e}", code="InitializationError"), file=sys.stdout)
        sys.exit(1)

    try:
        # Read request from stdin
        line = sys.stdin.readline()
        if not line:
            print(BridgeResponse.error("No input received", code="EOFError"), file=sys.stdout)
            sys.exit(1)

        # Parse request
        request = _parse_request(line.strip())

        method = request.get("method")
        args = request.get("args", {})
        kwargs = request.get("kwargs", {})

        # Execute command
        result = _execute_command(method, args, kwargs)

        # Extract notice if present (for market status)
        notice = _market_status.get("notice")

        # Write success response
        print(BridgeResponse.success(result, notice), file=sys.stdout)

    except Exception as e:
        import traceback

        # Write error response
        tb = traceback.format_exc()
        print(
            BridgeResponse.error(
                str(e),
                code=type(e).__name__,
                traceback=tb,
            ),
            file=sys.stdout,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
