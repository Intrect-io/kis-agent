/**
 * Python Bridge: TypeScript ↔ Python subprocess communication via execa
 *
 * Manages the lifecycle of the kis-cli-bridge Python subprocess and handles
 * JSON-based request/response communication over stdin/stdout pipes.
 *
 * Architecture:
 * - Uses execa for cross-platform process management
 * - Implements JSON-streaming protocol: one complete JSON per line
 * - Buffers incomplete lines until newline is received
 * - Supports request queuing and response matching
 */

import { execa, type ExecaChildProcess } from 'execa';
import { BridgeError, BridgeRequest, BridgeResponse } from './types.js';

/**
 * PythonBridge class manages the subprocess lifecycle and JSON communication.
 *
 * @example
 * ```typescript
 * const bridge = new PythonBridge();
 * await bridge.start();
 *
 * const response = await bridge.call({
 *   method: 'query',
 *   args: { domain: 'stock', method: 'get_stock_price', code: '005930' }
 * });
 *
 * console.log(response.data);
 * await bridge.stop();
 * ```
 */
export class PythonBridge {
  /**
   * Path to the Python subprocess entry point.
   * Should be the kis-cli-bridge module path.
   */
  private pythonScript: string;

  /**
   * The active subprocess instance.
   * null when bridge is not running.
   */
  private process: ExecaChildProcess<string> | null = null;

  /**
   * Buffer for incomplete input lines from stdout.
   * As stdout data arrives, it may be fragmented.
   * Incomplete lines are buffered until newline is received.
   */
  private outputBuffer: string = '';

  /**
   * Queue of pending requests waiting for responses.
   * Each request is paired with a Promise resolver to return the response.
   */
  private pendingRequests: Array<{
    request: BridgeRequest;
    resolve: (response: BridgeResponse) => void;
    reject: (error: Error) => void;
  }> = [];

  /**
   * Creates a new PythonBridge instance.
   *
   * @param pythonScript - Path to the kis-cli-bridge subprocess.
   *                      Defaults to 'kis_agent.cli.bridge' (Python module path)
   */
  constructor(pythonScript: string = 'kis_agent.cli.bridge') {
    this.pythonScript = pythonScript;
  }

  /**
   * Starts the Python subprocess.
   *
   * Spawns a new Python process running kis-cli-bridge and sets up stdin/stdout
   * communication pipelines.
   *
   * @throws {BridgeError} If subprocess fails to start
   *
   * @example
   * ```typescript
   * const bridge = new PythonBridge();
   * await bridge.start();
   * ```
   */
  public async start(): Promise<void> {
    if (this.process) {
      throw new BridgeError('Bridge is already running');
    }

    try {
      // Spawn Python subprocess with -m flag to run module
      this.process = execa('python3', ['-m', this.pythonScript], {
        stdin: 'pipe',
        stdout: 'pipe',
        stderr: 'pipe',
        // Use pipe instead of inherit to capture all output
        all: false,
      });

      // Handle stdout data: parse JSON lines and dispatch to pending requests
      if (this.process.stdout) {
        this.process.stdout.on('data', (data: Buffer) => {
          this.handleStdoutData(data);
        });
      }

      // Handle stderr output for debugging
      if (this.process.stderr) {
        this.process.stderr.on('data', (data: Buffer) => {
          // stderr is typically used for logging/debugging
          // Accumulated in case needed for error diagnostics
        });
      }

      // Handle process exit
      this.process.on('exit', (code: number | null) => {
        if (code !== 0 && code !== null) {
          this.process = null;
        }
      });

      // Wait briefly for subprocess to be ready
      // (Allow it to output any initialization messages)
      await new Promise((resolve) => setTimeout(resolve, 100));
    } catch (error) {
      this.process = null;
      throw new BridgeError(`Failed to start Python subprocess: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Stops the Python subprocess.
   *
   * Gracefully terminates the process and cleans up resources.
   *
   * @throws {BridgeError} If bridge is not running
   *
   * @example
   * ```typescript
   * await bridge.stop();
   * ```
   */
  public async stop(): Promise<void> {
    if (!this.process) {
      throw new BridgeError('Bridge is not running');
    }

    try {
      // Close stdin to signal EOF to subprocess
      if (this.process.stdin) {
        this.process.stdin.end();
      }

      // Wait for process to exit (with timeout)
      const exitPromise = new Promise<void>((resolve) => {
        if (!this.process) {
          resolve();
          return;
        }
        this.process.on('exit', () => {
          resolve();
        });
        // Timeout after 5 seconds, then force kill
        setTimeout(() => {
          if (this.process) {
            this.process.kill();
          }
          resolve();
        }, 5000);
      });

      await exitPromise;
      this.process = null;
      this.outputBuffer = '';
      this.pendingRequests = [];
    } catch (error) {
      this.process = null;
      throw new BridgeError(`Failed to stop Python subprocess: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Sends a request to the Python subprocess and waits for response.
   *
   * Protocol: Serializes request as JSON, sends via stdin with newline.
   * Response is parsed from stdout as JSON and matched to request.
   *
   * @param request - The BridgeRequest to send
   * @returns Promise resolving to the BridgeResponse from subprocess
   * @throws {BridgeError} If not running, serialization fails, or response is invalid
   *
   * @example
   * ```typescript
   * const response = await bridge.call({
   *   method: 'query',
   *   args: { domain: 'stock', method: 'get_stock_price', code: '005930' }
   * });
   *
   * if ('data' in response && !('error' in response)) {
   *   console.log(response.data);
   * } else {
   *   console.error(response.error);
   * }
   * ```
   */
  public async call(request: BridgeRequest): Promise<BridgeResponse> {
    if (!this.process || !this.process.stdin) {
      throw new BridgeError('Bridge is not running. Call start() first.');
    }

    try {
      // Serialize request to JSON and add newline
      const requestJson = JSON.stringify(request);
      const requestLine = requestJson + '\n';

      // Create promise that will be resolved when response arrives
      const responsePromise = new Promise<BridgeResponse>((resolve, reject) => {
        this.pendingRequests.push({ request, resolve, reject });
      });

      // Send request via stdin
      const sent = this.process.stdin!.write(requestLine);
      if (!sent) {
        // stdin buffer full - wait for drain event
        await new Promise<void>((resolve) => {
          this.process?.stdin?.once('drain', () => resolve());
        });
      }

      // Wait for response with timeout
      const timeoutPromise = new Promise<BridgeResponse>((_resolve, reject) => {
        setTimeout(() => {
          reject(new BridgeError('Request timeout: no response from Python subprocess'));
        }, 30000); // 30 second timeout
      });

      return await Promise.race([responsePromise, timeoutPromise]);
    } catch (error) {
      if (error instanceof BridgeError) {
        throw error;
      }
      throw new BridgeError(`Failed to send request: ${error instanceof Error ? error.message : String(error)}`, {
        request,
      });
    }
  }

  /**
   * Checks if the bridge is currently running.
   *
   * @returns true if subprocess is active and ready for requests
   */
  public isRunning(): boolean {
    return this.process !== null;
  }

  /**
   * Handles incoming data from subprocess stdout.
   *
   * Buffers partial lines and processes complete JSON lines.
   * Each complete line is parsed as a JSON response and dispatched to
   * the matching pending request.
   *
   * @param data - Raw buffer from stdout
   */
  private handleStdoutData(data: Buffer): void {
    const chunk = data.toString('utf8');
    this.outputBuffer += chunk;

    // Process all complete lines (ending with \n)
    const lines = this.outputBuffer.split('\n');

    // Keep the last incomplete line in buffer
    this.outputBuffer = lines[lines.length - 1];

    // Process all complete lines
    for (let i = 0; i < lines.length - 1; i++) {
      const line = lines[i].trim();
      if (line.length === 0) {
        // Skip empty lines
        continue;
      }

      try {
        const response: BridgeResponse = JSON.parse(line);
        this.dispatchResponse(response);
      } catch (parseError) {
        // JSON parse error - reject the oldest pending request
        const pending = this.pendingRequests.shift();
        if (pending) {
          pending.reject(
            new BridgeError('Failed to parse response from Python subprocess', {
              rawResponse: line,
              request: pending.request,
            })
          );
        }
      }
    }
  }

  /**
   * Dispatches a parsed response to the matching pending request.
   *
   * Resolves the Promise for the oldest pending request with the response.
   *
   * @param response - Parsed BridgeResponse from subprocess
   */
  private dispatchResponse(response: BridgeResponse): void {
    const pending = this.pendingRequests.shift();
    if (pending) {
      pending.resolve(response);
    }
  }
}
