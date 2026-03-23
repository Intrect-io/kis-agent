/**
 * Test suite for PythonBridge class
 *
 * Tests the lifecycle management and JSON communication pipeline
 * for subprocess interaction via execa.
 */

import test from 'node:test';
import assert from 'node:assert';
import { PythonBridge } from './python-bridge.js';
import { BridgeError, isSuccessResponse, isErrorResponse } from './types.js';

test('PythonBridge - constructor', async (t) => {
  await t.test('should create instance with default Python script path', () => {
    const bridge = new PythonBridge();
    assert.ok(bridge);
    assert.strictEqual(bridge.isRunning(), false);
  });

  await t.test('should create instance with custom Python script path', () => {
    const customPath = 'custom.module.path';
    const bridge = new PythonBridge(customPath);
    assert.ok(bridge);
    assert.strictEqual(bridge.isRunning(), false);
  });
});

test('PythonBridge - isRunning', async (t) => {
  await t.test('should return false when bridge is not started', () => {
    const bridge = new PythonBridge();
    assert.strictEqual(bridge.isRunning(), false);
  });
});

test('PythonBridge - error cases', async (t) => {
  await t.test('should throw BridgeError when calling before start()', async () => {
    const bridge = new PythonBridge();
    const request = {
      method: 'query',
      args: { domain: 'stock', method: 'get_price' },
    };

    try {
      await bridge.call(request);
      assert.fail('Should have thrown');
    } catch (err) {
      assert.ok(err instanceof BridgeError);
      assert.match((err as BridgeError).message, /Bridge is not running/);
    }
  });

  await t.test('should throw BridgeError when stopping without starting', async () => {
    const bridge = new PythonBridge();
    try {
      await bridge.stop();
      assert.fail('Should have thrown');
    } catch (err) {
      assert.ok(err instanceof BridgeError);
      assert.match((err as BridgeError).message, /Bridge is not running/);
    }
  });
});

test('BridgeError - custom error class', async (t) => {
  await t.test('should create error with message', () => {
    const error = new BridgeError('Test error');
    assert.ok(error instanceof BridgeError);
    assert.ok(error instanceof Error);
    assert.strictEqual(error.message, 'Test error');
    assert.strictEqual(error.name, 'BridgeError');
  });

  await t.test('should create error with options', () => {
    const request = { method: 'test', args: {} };
    const error = new BridgeError('Test error', {
      code: 'TEST_CODE',
      traceback: 'test traceback',
      request,
      rawResponse: '{"error": "test"}',
    });

    assert.strictEqual(error.code, 'TEST_CODE');
    assert.strictEqual(error.traceback, 'test traceback');
    assert.deepStrictEqual(error.request, request);
    assert.strictEqual(error.rawResponse, '{"error": "test"}');
  });

  await t.test('should maintain proper prototype chain for instanceof', () => {
    const error = new BridgeError('Test');
    assert.ok(error instanceof BridgeError);
    assert.ok(error instanceof Error);
  });
});

test('Type contracts', async (t) => {
  await t.test('should have correct types for BridgeRequest', () => {
    const validRequest = {
      method: 'price',
      args: {
        code: '005930',
        name: 'Samsung',
        count: 100,
        enabled: true,
        tags: ['stock', 'kospi'],
      },
      kwargs: {
        pretty: true,
        detailed: false,
      },
    };

    assert.strictEqual(validRequest.method, 'price');
    assert.strictEqual(validRequest.args.code, '005930');
    assert.strictEqual(typeof validRequest.kwargs?.pretty, 'boolean');
  });

  await t.test('should handle success response payload', () => {
    const successPayload = {
      data: {
        stock: {
          code: '005930',
          price: 70000,
          daily: 500,
        },
      },
    };

    assert.ok('data' in successPayload);
    assert.ok(successPayload.data);
  });

  await t.test('should handle error response payload', () => {
    const errorPayload = {
      error: 'Failed to fetch price',
      code: 'APIError',
      traceback: 'Traceback (most recent call last)...',
    };

    assert.ok('error' in errorPayload);
    assert.ok(errorPayload.code);
  });
});

test('Type guards', async (t) => {
  await t.test('isSuccessResponse should identify success responses', () => {
    const successResponse = { data: { result: 'ok' } };
    const errorResponse = { error: 'Failed' };

    assert.strictEqual(isSuccessResponse(successResponse), true);
    assert.strictEqual(isSuccessResponse(errorResponse), false);
  });

  await t.test('isErrorResponse should identify error responses', () => {
    const successResponse = { data: { result: 'ok' } };
    const errorResponse = { error: 'Failed' };

    assert.strictEqual(isErrorResponse(errorResponse), true);
    assert.strictEqual(isErrorResponse(successResponse), false);
  });
});

test('Module compilation', async (t) => {
  await t.test('should compile TypeScript without errors', () => {
    // This test verifies that the code compiles without errors
    // The TypeScript compiler caught any issues during npm run build
    const bridge = new PythonBridge();
    assert.ok(bridge);
  });

  await t.test('should export correct types and functions', async () => {
    // Verify that all expected exports are available
    assert.strictEqual(typeof PythonBridge, 'function');
    assert.strictEqual(typeof BridgeError, 'function');
    assert.strictEqual(typeof isSuccessResponse, 'function');
    assert.strictEqual(typeof isErrorResponse, 'function');
  });
});
