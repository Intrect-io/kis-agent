/**
 * PythonBridge 생명 주기 관리 테스트
 */

import { PythonBridge } from '../python-bridge.js';
import { ProcessState } from '../../types/python-bridge.js';

describe('PythonBridge', () => {
  let bridge: PythonBridge;

  beforeEach(() => {
    bridge = new PythonBridge({
      timeout: 10000,
    });
  });

  describe('initialization', () => {
    it('should initialize with default config', () => {
      const info = bridge.getProcessInfo();
      expect(info.pythonExecutable).toBe('python3');
      expect(info.cliModule).toBe('kis');
      expect(info.timeout).toBe(10000);
    });

    it('should initialize with custom config', () => {
      const customBridge = new PythonBridge({
        pythonExecutable: 'python',
        cliModule: 'kis_agent',
        timeout: 20000,
      });
      const info = customBridge.getProcessInfo();
      expect(info.pythonExecutable).toBe('python');
      expect(info.cliModule).toBe('kis_agent');
      expect(info.timeout).toBe(20000);
    });
  });

  describe('process lifecycle', () => {
    it('should have initial IDLE state', () => {
      const status = bridge.getStatus();
      expect(status.state).toBe(ProcessState.IDLE);
      expect(status.pid).toBeUndefined();
    });

    it('should transition to RUNNING on start attempt', async () => {
      const startResult = await bridge.start();
      const status = bridge.getStatus();

      // Python 설치 여부에 따라 결과가 결정됨
      if (startResult) {
        expect([ProcessState.IDLE, ProcessState.RUNNING]).toContain(
          status.state
        );
      } else {
        expect(status.state).toBe(ProcessState.ERROR);
      }
    });

    it('should transition to STOPPED on stop', async () => {
      await bridge.start();
      await bridge.stop();
      const status = bridge.getStatus();
      expect(status.state).toBe(ProcessState.STOPPED);
    });

    it('should handle restart', async () => {
      const restartResult = await bridge.restart();
      const status = bridge.getStatus();

      // 재시작 결과에 따라 상태 확인
      if (restartResult) {
        expect([ProcessState.IDLE, ProcessState.RUNNING]).toContain(
          status.state
        );
      } else {
        expect(status.state).toBe(ProcessState.ERROR);
      }
    });
  });

  describe('environment variables', () => {
    it('should get environment variables', () => {
      const envVars = bridge.getEnvVars();
      expect(typeof envVars).toBe('object');
    });

    it('should set and retrieve environment variables', () => {
      bridge.setEnvVar('TEST_VAR', 'test_value');
      const envVars = bridge.getEnvVars();
      expect(envVars.TEST_VAR).toBe('test_value');
    });

    it('should remove environment variables', () => {
      bridge.setEnvVar('TEST_VAR', 'test_value');
      bridge.removeEnvVar('TEST_VAR');
      const envVars = bridge.getEnvVars();
      expect(envVars.TEST_VAR).toBeUndefined();
    });
  });

  describe('validation', () => {
    it('should validate required environment variables', () => {
      const result = bridge.validateRequiredEnvVars(['PATH']);
      expect(result.valid).toBe(true);
      expect(result.missing.length).toBe(0);
    });

    it('should detect missing environment variables', () => {
      const result = bridge.validateRequiredEnvVars([
        'NONEXISTENT_VAR_12345',
      ]);
      expect(result.valid).toBe(false);
      expect(result.missing).toContain('NONEXISTENT_VAR_12345');
    });

    it('should validate Python installation', async () => {
      const isValid = await bridge.validatePython();
      expect(typeof isValid).toBe('boolean');

      if (isValid) {
        const status = bridge.getStatus();
        expect(status.state).not.toBe(ProcessState.ERROR);
      }
    });
  });

  describe('error handling', () => {
    it('should handle invalid command gracefully', async () => {
      const result = await bridge.call('invalid-command-12345');
      expect(result.error).toBeDefined();
      expect(result.error).toMatch(/error|not found|command/i);
    });

    it('should capture error state', async () => {
      await bridge.call('invalid-command-12345');
      const status = bridge.getStatus();
      expect(status.lastError).toBeInstanceOf(Error);
    });
  });

  describe('process info', () => {
    it('should return complete process info', () => {
      const info = bridge.getProcessInfo();
      expect(info).toHaveProperty('pythonExecutable');
      expect(info).toHaveProperty('cliModule');
      expect(info).toHaveProperty('timeout');
      expect(info).toHaveProperty('envFile');
      expect(info).toHaveProperty('status');
    });
  });
});
