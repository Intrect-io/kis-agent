/**
 * Python 환경 검증 유틸리티
 */

import { execa } from 'execa';

/**
 * Python 설치 확인 및 버전 조회
 */
export async function checkPythonInstallation(
  pythonPath: string = 'python3'
): Promise<{
  installed: boolean;
  version?: string;
  error?: string;
}> {
  try {
    const { stdout } = await execa(pythonPath, ['--version'], {
      timeout: 5000,
    });
    const versionMatch = stdout.match(/Python\s+([\d.]+)/);
    const version = versionMatch ? versionMatch[1] : stdout.trim();

    return {
      installed: true,
      version,
    };
  } catch (error) {
    return {
      installed: false,
      error: (error as Error).message,
    };
  }
}

/**
 * Python 패키지 설치 확인
 */
export async function checkPythonPackage(
  packageName: string,
  pythonPath: string = 'python3'
): Promise<{
  installed: boolean;
  version?: string;
  error?: string;
}> {
  try {
    const { stdout } = await execa(pythonPath, [
      '-m',
      'pip',
      'show',
      packageName,
    ], {
      timeout: 10000,
    });

    const versionMatch = stdout.match(/Version:\s+([\d.]+)/);
    const version = versionMatch ? versionMatch[1] : undefined;

    return {
      installed: true,
      version,
    };
  } catch (error) {
    return {
      installed: false,
      error: (error as Error).message,
    };
  }
}

/**
 * Python CLI 모듈 검증
 */
export async function validatePythonModule(
  moduleName: string,
  pythonPath: string = 'python3',
  timeoutMs: number = 5000
): Promise<{
  valid: boolean;
  error?: string;
}> {
  try {
    await execa(pythonPath, ['-c', `import ${moduleName}`], {
      timeout: timeoutMs,
    });
    return { valid: true };
  } catch (error) {
    return {
      valid: false,
      error: (error as Error).message,
    };
  }
}

/**
 * kis CLI 가용성 확인
 */
export async function checkKisCLI(
  pythonPath: string = 'python3'
): Promise<{
  available: boolean;
  method?: 'direct' | 'module';
  error?: string;
}> {
  // 직접 실행 시도
  try {
    await execa('kis', ['--version'], { timeout: 5000 });
    return { available: true, method: 'direct' };
  } catch {
    // kis 직접 실행 실패 → Python 모듈로 시도
    try {
      await execa(pythonPath, ['-m', 'kis_agent.cli.main', '--version'], {
        timeout: 5000,
      });
      return { available: true, method: 'module' };
    } catch (error) {
      return {
        available: false,
        error: (error as Error).message,
      };
    }
  }
}

/**
 * 환경 진단 (전체 체크)
 */
export async function diagnoseEnvironment(
  pythonPath: string = 'python3'
): Promise<{
  python: { installed: boolean; version?: string };
  kisPackage: { installed: boolean; version?: string };
  kisCLI: { available: boolean; method?: string };
  summary: string;
}> {
  const [pythonCheck, kisCheck, cliCheck] = await Promise.all([
    checkPythonInstallation(pythonPath),
    checkPythonPackage('kis-agent', pythonPath),
    checkKisCLI(pythonPath),
  ]);

  let summary = '';
  if (!pythonCheck.installed) {
    summary = `Python not found at ${pythonPath}`;
  } else if (!kisCheck.installed) {
    summary = 'kis-agent package not installed';
  } else if (!cliCheck.available) {
    summary = 'kis CLI not accessible';
  } else {
    summary = 'Environment OK';
  }

  return {
    python: {
      installed: pythonCheck.installed,
      version: pythonCheck.version,
    },
    kisPackage: {
      installed: kisCheck.installed,
      version: kisCheck.version,
    },
    kisCLI: {
      available: cliCheck.available,
      method: cliCheck.method,
    },
    summary,
  };
}
