/**
 * Python Bridge
 * KIS Python CLI를 subprocess로 호출하고 결과를 처리하는 클래스
 */

import { execa } from 'execa';
import path from 'path';
import fs from 'fs';
import dotenv from 'dotenv';

import type {
  PythonBridgeConfig,
  ProcessStatus,
  BridgeCallResult,
} from '../types/python-bridge.js';
import { ProcessState as ProcessStateEnum } from '../types/python-bridge.js';

export class PythonBridge {
  private pythonExecutable: string;
  private envFile: string;
  private timeout: number;
  private cliModule: string;
  private envVars: Record<string, string | undefined>;
  private processStatus: ProcessStatus;

  constructor(config: PythonBridgeConfig = {}) {
    this.pythonExecutable = config.pythonExecutable || 'python3';
    this.cliModule = config.cliModule || 'kis';
    this.timeout = config.timeout || 30000;

    // .env 파일 경로 결정
    if (config.envFile) {
      this.envFile = config.envFile;
    } else {
      // 프로젝트 루트 기준 .env 찾기
      const projectRoot = this.findProjectRoot();
      this.envFile = path.join(projectRoot, '.env');
    }

    // 환경변수 초기화 (process.env는 Record<string, string | undefined> 타입)
    this.envVars = { ...process.env };
    this.loadEnvFile();

    // 프로세스 상태 초기화
    this.processStatus = {
      state: ProcessStateEnum.IDLE,
      pid: undefined,
      lastError: undefined,
      startTime: undefined,
    };
  }

  /**
   * 에러 메시지 추출
   */
  private extractErrorMessage(error: any): string {
    if (!error) return 'Unknown error occurred';
    if (typeof error === 'string') return error;
    if (error instanceof Error) return error.message;
    if (error.message) return String(error.message);
    if (error.stderr) return String(error.stderr);
    if (error.stdout) return String(error.stdout);
    return 'Unknown error occurred';
  }

  /**
   * 프로젝트 루트 디렉토리 찾기 (package.json 위치)
   */
  private findProjectRoot(): string {
    let currentDir = process.cwd();
    const root = path.parse(currentDir).root;

    while (currentDir !== root) {
      const packageJsonPath = path.join(currentDir, 'package.json');
      if (fs.existsSync(packageJsonPath)) {
        return currentDir;
      }
      currentDir = path.dirname(currentDir);
    }

    return process.cwd();
  }

  /**
   * .env 파일에서 환경변수 로드
   */
  private loadEnvFile(): void {
    if (fs.existsSync(this.envFile)) {
      const envConfig = dotenv.parse(fs.readFileSync(this.envFile, 'utf-8'));
      this.envVars = { ...process.env, ...envConfig };
    }
  }

  /**
   * Python 실행 파일 검증
   */
  async validatePython(): Promise<boolean> {
    try {
      const { stdout } = await execa(this.pythonExecutable, ['--version'], {
        timeout: 5000,
      });
      return stdout.includes('Python') || stdout.includes('python');
    } catch (error) {
      this.processStatus = {
        state: ProcessStateEnum.ERROR,
        lastError: error as Error,
      };
      return false;
    }
  }

  /**
   * KIS CLI 검증 (kis 명령 존재 확인)
   */
  async validateCLI(): Promise<boolean> {
    try {
      const { stdout } = await execa(this.cliModule, ['--version'], {
        timeout: 5000,
        env: this.envVars,
      });
      return stdout.length > 0;
    } catch (error) {
      // kis 명령이 직접 실행 가능하지 않을 수도 있음
      // Python 모듈로 호출 가능한지 확인
      try {
        const { stdout } = await execa(
          this.pythonExecutable,
          ['-m', this.cliModule, '--version'],
          {
            timeout: 5000,
            env: this.envVars,
          }
        );
        return stdout.length > 0;
      } catch {
        this.processStatus = {
          state: ProcessStateEnum.ERROR,
          lastError: new Error(`CLI module '${this.cliModule}' not found`),
        };
        return false;
      }
    }
  }

  /**
   * Python CLI 명령 호출
   * @param command - CLI 명령 (예: "price", "balance")
   * @param args - 명령 인자
   * @returns 명령 실행 결과
   */
  async call(
    command: string,
    ...args: string[]
  ): Promise<BridgeCallResult> {
    try {
      // 상태 업데이트
      this.processStatus.state = ProcessStateEnum.RUNNING;
      this.processStatus.startTime = new Date();

      const result = await execa(this.cliModule, [command, ...args], {
        timeout: this.timeout,
        env: this.envVars,
        stdin: 'pipe',
      });

      this.processStatus.state = ProcessStateEnum.IDLE;

      // JSON 응답 파싱 시도
      try {
        return JSON.parse(result.stdout) as BridgeCallResult;
      } catch {
        // JSON이 아닌 경우 원본 반환
        return {
          data: result.stdout,
        };
      }
    } catch (error) {
      const errorObj = error as any;
      const errorMessage = this.extractErrorMessage(errorObj);

      this.processStatus.state = ProcessStateEnum.ERROR;
      this.processStatus.lastError = new Error(errorMessage);

      return {
        error: errorMessage,
      };
    }
  }

  /**
   * 환경변수 조회
   */
  getEnvVars(): Record<string, string | undefined> {
    return { ...this.envVars };
  }

  /**
   * 환경변수 설정
   */
  setEnvVar(key: string, value: string | undefined): void {
    this.envVars[key] = value;
  }

  /**
   * 환경변수 제거
   */
  removeEnvVar(key: string): void {
    delete this.envVars[key];
  }

  /**
   * 프로세스 상태 조회
   */
  getStatus(): ProcessStatus {
    return { ...this.processStatus };
  }

  /**
   * Python 프로세스 시작 (유효성 검증)
   */
  async start(): Promise<boolean> {
    try {
      this.processStatus.state = ProcessStateEnum.RUNNING;
      this.processStatus.startTime = new Date();

      const pythonValid = await this.validatePython();
      if (!pythonValid) {
        throw new Error('Python validation failed');
      }

      const cliValid = await this.validateCLI();
      if (!cliValid) {
        throw new Error('CLI validation failed');
      }

      this.processStatus.state = ProcessStateEnum.IDLE;
      return true;
    } catch (error) {
      this.processStatus.state = ProcessStateEnum.ERROR;
      this.processStatus.lastError = error as Error;
      return false;
    }
  }

  /**
   * Python 프로세스 종료
   */
  async stop(): Promise<void> {
    this.processStatus = {
      state: ProcessStateEnum.STOPPED,
      pid: undefined,
      startTime: undefined,
      lastError: this.processStatus.lastError,
    };
  }

  /**
   * Python 프로세스 재시작
   */
  async restart(): Promise<boolean> {
    await this.stop();
    return this.start();
  }

  /**
   * 필수 환경변수 확인
   */
  validateRequiredEnvVars(required: string[]): {
    valid: boolean;
    missing: string[];
  } {
    const missing = required.filter((key) => !this.envVars[key]);
    return {
      valid: missing.length === 0,
      missing,
    };
  }

  /**
   * Python 프로세스 정보 조회
   */
  getProcessInfo(): {
    pythonExecutable: string;
    cliModule: string;
    timeout: number;
    envFile: string;
    status: ProcessStatus;
  } {
    return {
      pythonExecutable: this.pythonExecutable,
      cliModule: this.cliModule,
      timeout: this.timeout,
      envFile: this.envFile,
      status: this.getStatus(),
    };
  }
}

export type { BridgeCallResult, ProcessStatus } from '../types/python-bridge.js';
export { ProcessState as ProcessStateEnum } from '../types/python-bridge.js';
