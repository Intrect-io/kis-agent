/**
 * Python Bridge 타입 정의
 * KIS Python CLI와 TypeScript 간 인터페이스
 */

export interface PythonBridgeConfig {
  /** Python 실행 파일 경로 (기본값: "python3") */
  pythonExecutable?: string;
  /** .env 파일 경로 (기본값: 프로젝트 루트/.env) */
  envFile?: string;
  /** 프로세스 타임아웃 (밀리초, 기본값: 30000) */
  timeout?: number;
  /** Python CLI 모듈 경로 (기본값: "kis") */
  cliModule?: string;
}

export interface BridgeResult<T = unknown> {
  data?: T;
  error?: string;
  _notice?: string;
}

export interface StockPriceData {
  stock: {
    code: string;
    name?: string;
    price: Record<string, unknown>;
    daily?: Array<Record<string, unknown>>;
  };
}

export interface BalanceData {
  account?: {
    number: string;
    code?: string;
    balance?: Record<string, unknown>;
  };
  holdings?: Array<{
    code: string;
    name?: string;
    quantity: number;
    [key: string]: unknown;
  }>;
}

export interface QueryResult {
  [key: string]: unknown;
}

export type BridgeCallResult = BridgeResult<unknown>;

export enum ProcessState {
  IDLE = "IDLE",
  RUNNING = "RUNNING",
  STOPPED = "STOPPED",
  ERROR = "ERROR",
}

export interface ProcessStatus {
  state: ProcessState;
  pid?: number;
  lastError?: Error;
  startTime?: Date;
}
