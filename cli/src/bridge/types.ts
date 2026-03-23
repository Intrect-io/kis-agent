/**
 * TypeScript Bridge Types for kis-agent JSON subprocess communication
 *
 * This module defines the type contracts for JSON-based communication between
 * TypeScript CLI and Python subprocess (kis-cli-bridge).
 *
 * Protocol:
 * - Request: TypeScript → Python (stdin)
 * - Response: Python → TypeScript (stdout)
 * - Format: JSON lines (one complete JSON object per line)
 */

/**
 * Base type for command arguments
 */
export type CommandArgs = Record<string, string | number | boolean | string[]>;

/**
 * Bridge Request: TypeScript CLI → Python subprocess
 *
 * Sent via stdin to kis-cli-bridge subprocess.
 *
 * @example
 * ```json
 * {
 *   "method": "query",
 *   "args": {
 *     "domain": "stock",
 *     "method": "get_stock_price",
 *     "code": "005930"
 *   },
 *   "kwargs": {
 *     "pretty": false
 *   }
 * }
 * ```
 */
export interface BridgeRequest {
  /**
   * CLI command method to execute
   * Examples: "price", "balance", "query", "schema", "futures", "overseas", "orderbook"
   */
  method: string;

  /**
   * Positional and keyword arguments for the command
   * Key-value pairs passed to the command handler
   *
   * For query command:
   * - domain: API domain (stock, account, overseas, futures, overseas_futures)
   * - method: API method name
   * - [additional key=value pairs]: method arguments
   *
   * For other commands:
   * - code: stock/futures code
   * - excd: exchange code (for overseas)
   * - symb: symbol (for overseas)
   */
  args: CommandArgs;

  /**
   * Optional flags/options for the command
   * Examples: pretty, json, daily, detail, holdings, orderbook, overseas, option
   */
  kwargs?: Record<string, boolean | string | number>;
}

/**
 * Success Response Payload
 *
 * Used when command execution succeeds.
 */
export interface SuccessPayload {
  /**
   * Result data from successful command execution
   *
   * Structure depends on the command:
   * - price: { stock: { code, name?, price, daily? } }
   * - balance: { account: { balance, holdings? } }
   * - query: raw API response data
   * - schema: schema type definitions
   * - etc.
   */
  data: unknown;
}

/**
 * Error Response Payload
 *
 * Used when command execution fails.
 */
export interface ErrorPayload {
  /**
   * Human-readable error message
   */
  error: string;

  /**
   * Error code/type
   * Examples: "FileNotFoundError", "ValueError", "APIError", "AuthenticationError"
   */
  code?: string;

  /**
   * Optional stack trace for debugging
   */
  traceback?: string;
}

/**
 * Bridge Response: Python subprocess → TypeScript CLI
 *
 * Returned via stdout from kis-cli-bridge.
 * Exactly one of `data` or `error` will be present.
 */
export type BridgeResponse = SuccessPayload | ErrorPayload;

/**
 * Type guard to check if response is successful
 *
 * @param response - The response object
 * @returns true if response contains success data
 *
 * @example
 * ```typescript
 * if (isSuccessResponse(response)) {
 *   console.log(response.data);
 * } else {
 *   console.error(response.error);
 * }
 * ```
 */
export function isSuccessResponse(response: BridgeResponse): response is SuccessPayload {
  return 'data' in response && !('error' in response);
}

/**
 * Type guard to check if response is an error
 *
 * @param response - The response object
 * @returns true if response contains error
 *
 * @example
 * ```typescript
 * if (isErrorResponse(response)) {
 *   console.error(`Error: ${response.error} (${response.code})`);
 * }
 * ```
 */
export function isErrorResponse(response: BridgeResponse): response is ErrorPayload {
  return 'error' in response && !('data' in response);
}

/**
 * BridgeError: Custom error class for bridge communication failures
 *
 * Used to represent errors that occur during subprocess communication,
 * parsing, or execution.
 *
 * @example
 * ```typescript
 * try {
 *   const response = await sendRequest(request);
 * } catch (err) {
 *   if (err instanceof BridgeError) {
 *     console.error(`Bridge error: ${err.message} (code: ${err.code})`);
 *   }
 * }
 * ```
 */
export class BridgeError extends Error {
  /**
   * Error code from Python subprocess or bridge layer
   */
  code?: string;

  /**
   * Original Python traceback (if available)
   */
  traceback?: string;

  /**
   * The request that caused the error
   */
  request?: BridgeRequest;

  /**
   * The raw response from subprocess (if available)
   */
  rawResponse?: string;

  constructor(
    message: string,
    options?: {
      code?: string;
      traceback?: string;
      request?: BridgeRequest;
      rawResponse?: string;
    }
  ) {
    super(message);
    this.name = 'BridgeError';
    this.code = options?.code;
    this.traceback = options?.traceback;
    this.request = options?.request;
    this.rawResponse = options?.rawResponse;

    // Maintain proper prototype chain for instanceof checks
    Object.setPrototypeOf(this, BridgeError.prototype);
  }
}

/**
 * Special marker for market status notices
 *
 * When the market is closed or during off-hours,
 * Python responses may include a _notice field.
 *
 * @example
 * ```json
 * {
 *   "data": { ... },
 *   "_notice": "휴장일 — 데이터는 직전 영업일(2026-03-20 금) 기준"
 * }
 * ```
 */
export interface BridgeResponseWithNotice extends SuccessPayload {
  _notice?: string;
}
