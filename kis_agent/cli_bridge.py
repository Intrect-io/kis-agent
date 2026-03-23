#!/usr/bin/env python3
"""kis-cli-bridge: Python subprocess entry point for JSON-based CLI communication.

This module implements a JSON streaming protocol for TypeScript ↔ Python subprocess communication.

Protocol:
- Input:  JSON line (newline-delimited) with {method, args, kwargs}
- Output: JSON line with {data, ...} or {error, code, traceback}

Example request:
  {"method": "price", "args": {"code": "005930"}, "kwargs": {}}

Example response (success):
  {"data": {"stock": {...}}, "_notice": "..."}

Example response (error):
  {"error": "...", "code": "ValueError", "traceback": "..."}
"""

import io
import json
import sys
import traceback
from types import SimpleNamespace
from typing import Any, Dict, Optional

from kis_agent.cli.main import (
    cmd_balance,
    cmd_futures,
    cmd_orderbook,
    cmd_overseas,
    cmd_price,
    cmd_query,
    cmd_schema,
    _check_market_status,
    _create_agent,
    _market_status,
)


class BridgeResponse:
    """Helper class for creating structured JSON responses."""

    @staticmethod
    def success(data: Any, notice: Optional[str] = None) -> str:
        """Create a success response JSON string.

        Args:
            data: The result data to return
            notice: Optional notice message (e.g., market status)

        Returns:
            JSON string with {data, ...} structure
        """
        response: Dict[str, Any] = {"data": data}
        if notice:
            response["_notice"] = notice
        return json.dumps(response, ensure_ascii=False, default=str)

    @staticmethod
    def error(
        message: str, code: str = "Error", tb: Optional[str] = None
    ) -> str:
        """Create an error response JSON string.

        Args:
            message: Error message
            code: Error code (e.g., ValueError, FileNotFoundError)
            tb: Optional traceback string

        Returns:
            JSON string with {error, code, ...} structure
        """
        response: Dict[str, Any] = {"error": message, "code": code}
        if tb:
            response["traceback"] = tb
        return json.dumps(response, ensure_ascii=False, default=str)


def _parse_request(line: str) -> Dict[str, Any]:
    """Parse a JSON request line.

    Args:
        line: JSON string from stdin

    Returns:
        Parsed request dict with keys: method, args, kwargs

    Raises:
        ValueError: If JSON is invalid
        KeyError: If required fields are missing
    """
    try:
        request = json.loads(line)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    if not isinstance(request, dict):
        raise ValueError("Request must be a JSON object")

    method = request.get("method")
    if not method or not isinstance(method, str):
        raise ValueError("Request must have 'method' field (string)")

    args = request.get("args", {})
    if not isinstance(args, dict):
        raise ValueError("'args' field must be a dict")

    kwargs = request.get("kwargs", {})
    if not isinstance(kwargs, dict):
        raise ValueError("'kwargs' field must be a dict")

    return {"method": method, "args": args, "kwargs": kwargs}


def _execute_command(method: str, args: Dict[str, Any], kwargs: Dict[str, Any]) -> Any:
    """Execute a CLI command handler based on method name.

    Args:
        method: Command method name (e.g., "price", "balance")
        args: Positional arguments as dict
        kwargs: Keyword arguments (flags)

    Returns:
        Command result (the result is printed to stdout by the handler)

    Raises:
        ValueError: If method is unknown
        Exception: If handler execution fails
    """
    # Create a namespace object combining args and kwargs
    # This mimics argparse.Namespace used by CLI handlers
    ns = SimpleNamespace(**args, **kwargs)

    # Map method names to handler functions
    handlers: Dict[str, Any] = {
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
        raise ValueError(f"Unknown command: {method}")

    # Capture stdout to get JSON output from handler
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        # Execute handler — it will print JSON to stdout
        handler(ns)
        output = sys.stdout.getvalue()

        # The handler prints JSON with _out(), so we parse and return it
        if output:
            try:
                return json.loads(output.strip())
            except json.JSONDecodeError:
                # Fallback if handler didn't produce valid JSON
                return {"data": output}
        else:
            return {"data": None}
    finally:
        sys.stdout = old_stdout


def main() -> None:
    """Main bridge loop — read BridgeRequest from stdin, write BridgeResponse to stdout.

    Protocol:
    1. Initialize Agent once (sets market status)
    2. Read one JSON line from stdin (blocking)
    3. Parse request: {method, args, kwargs}
    4. Execute command handler
    5. Write JSON response to stdout
    6. Exit

    Error handling:
    - Parse errors → error response with code
    - Unknown method → error response with ValueError
    - Handler exceptions → error response with traceback
    """
    try:
        # Create agent once — this sets market status
        agent = _create_agent()
    except Exception as e:
        error_response = BridgeResponse.error(
            f"Failed to create agent: {str(e)}",
            "InitError",
            traceback.format_exc(),
        )
        print(error_response, file=sys.stdout)
        sys.exit(1)

    try:
        # Read one line from stdin (request)
        line = sys.stdin.readline()
        if not line:
            # stdin closed without request
            error_response = BridgeResponse.error("No input on stdin", "EOFError")
            print(error_response, file=sys.stdout)
            sys.exit(1)

        # Parse request
        request = _parse_request(line.strip())
        method = request["method"]
        args = request["args"]
        kwargs = request["kwargs"]

        # Execute command
        result = _execute_command(method, args, kwargs)

        # Get market status notice if any
        notice = _market_status.get("notice")

        # Send success response
        response = BridgeResponse.success(result, notice)
        print(response, file=sys.stdout)

    except ValueError as e:
        # Invalid request format
        error_response = BridgeResponse.error(str(e), "ValueError")
        print(error_response, file=sys.stdout)
        sys.exit(1)
    except Exception as e:
        # Unexpected exception
        error_response = BridgeResponse.error(
            str(e), type(e).__name__, traceback.format_exc()
        )
        print(error_response, file=sys.stdout)
        sys.exit(1)


if __name__ == "__main__":
    main()
