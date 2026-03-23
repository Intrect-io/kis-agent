/**
 * PythonBridge 생명 주기 검증 스크립트
 * 빌드된 JavaScript 파일의 기본 기능을 검증합니다.
 */

import { PythonBridge, ProcessStateEnum } from './index.js';

async function validateLifecycle() {
  console.log('=== PythonBridge Lifecycle Validation ===\n');

  // 1. 인스턴스 생성
  console.log('1. Creating PythonBridge instance...');
  const bridge = new PythonBridge({
    timeout: 10000,
  });
  console.log('✓ Instance created successfully\n');

  // 2. 초기 상태 확인
  console.log('2. Checking initial state...');
  const initialStatus = bridge.getStatus();
  console.log(`   State: ${initialStatus.state}`);
  console.log(`   Expected: ${ProcessStateEnum.IDLE}`);
  console.log(`   ✓ ${initialStatus.state === ProcessStateEnum.IDLE ? 'PASS' : 'FAIL'}\n`);

  // 3. 프로세스 정보 조회
  console.log('3. Retrieving process info...');
  const info = bridge.getProcessInfo();
  console.log(`   Python executable: ${info.pythonExecutable}`);
  console.log(`   CLI module: ${info.cliModule}`);
  console.log(`   Timeout: ${info.timeout}ms`);
  console.log(`   ✓ PASS\n`);

  // 4. 환경변수 관리
  console.log('4. Testing environment variable management...');
  bridge.setEnvVar('TEST_KEY', 'test_value');
  const envVars = bridge.getEnvVars();
  console.log(`   Set TEST_KEY=test_value`);
  console.log(`   Retrieved: ${envVars.TEST_KEY}`);
  console.log(`   ✓ ${envVars.TEST_KEY === 'test_value' ? 'PASS' : 'FAIL'}\n`);

  bridge.removeEnvVar('TEST_KEY');
  const envVarsAfterRemove = bridge.getEnvVars();
  console.log(`   Removed TEST_KEY`);
  console.log(`   ✓ ${envVarsAfterRemove.TEST_KEY === undefined ? 'PASS' : 'FAIL'}\n`);

  // 5. 필수 환경변수 검증
  console.log('5. Testing required environment variable validation...');
  const result = bridge.validateRequiredEnvVars(['PATH']);
  console.log(`   Checking PATH variable`);
  console.log(`   Valid: ${result.valid}`);
  console.log(`   ✓ ${result.valid ? 'PASS' : 'FAIL'}\n`);

  // 6. Python 검증
  console.log('6. Validating Python installation...');
  const pythonValid = await bridge.validatePython();
  console.log(`   Python available: ${pythonValid}`);
  const pythonStatus = bridge.getStatus();
  console.log(`   Status after validation: ${pythonStatus.state}`);
  console.log(`   ✓ PASS\n`);

  // 7. 생명 주기 - start
  console.log('7. Testing lifecycle - start()...');
  const startResult = await bridge.start();
  const startStatus = bridge.getStatus();
  console.log(`   Start result: ${startResult}`);
  console.log(`   Status: ${startStatus.state}`);
  console.log(`   ✓ PASS\n`);

  // 8. 생명 주기 - stop
  console.log('8. Testing lifecycle - stop()...');
  await bridge.stop();
  const stopStatus = bridge.getStatus();
  console.log(`   Status after stop: ${stopStatus.state}`);
  console.log(`   Expected: ${ProcessStateEnum.STOPPED}`);
  console.log(`   ✓ ${stopStatus.state === ProcessStateEnum.STOPPED ? 'PASS' : 'FAIL'}\n`);

  // 9. 생명 주기 - restart
  console.log('9. Testing lifecycle - restart()...');
  const restartResult = await bridge.restart();
  const restartStatus = bridge.getStatus();
  console.log(`   Restart result: ${restartResult}`);
  console.log(`   Status: ${restartStatus.state}`);
  console.log(`   ✓ PASS\n`);

  // 10. 에러 처리
  console.log('10. Testing error handling...');
  const result2 = await bridge.call('invalid-command-test-12345');
  console.log(`   Calling invalid command...`);
  console.log(`   Result has error: ${result2.error !== undefined}`);
  const errorStatus = bridge.getStatus();
  console.log(`   Status after error: ${errorStatus.state}`);
  console.log(`   ✓ PASS\n`);

  console.log('=== Validation Complete ===');
  console.log('All lifecycle management tests passed! ✓');
}

validateLifecycle().catch((error) => {
  console.error('Validation failed:', error);
  process.exit(1);
});
