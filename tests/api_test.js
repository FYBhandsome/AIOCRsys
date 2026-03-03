/**
 * 自动化测试脚本
 * 用于测试所有后端API接口和前端功能
 */

const axios = require('axios');

const BASE_URL = 'http://localhost:8001';
const RAG_URL = 'http://localhost:8010';

const testResults = {
  passed: [],
  failed: [],
  total: 0
};

async function testAPI(name, url, expectedStatus = 200) {
  testResults.total++;
  try {
    const response = await axios.get(url, { timeout: 5000 });
    if (response.status === expectedStatus) {
      testResults.passed.push({ name, url });
      console.log(`✅ [PASS] ${name}: ${url}`);
      return true;
    } else {
      testResults.failed.push({ name, url, error: `Expected ${expectedStatus}, got ${response.status}` });
      console.log(`❌ [FAIL] ${name}: ${url} - Expected ${expectedStatus}, got ${response.status}`);
      return false;
    }
  } catch (error) {
    testResults.failed.push({ name, url, error: error.message });
    console.log(`❌ [FAIL] ${name}: ${url} - ${error.message}`);
    return false;
  }
}

async function testPostAPI(name, url, data, expectedStatus = 200) {
  testResults.total++;
  try {
    const response = await axios.post(url, data, { timeout: 10000 });
    if (response.status === expectedStatus) {
      testResults.passed.push({ name, url });
      console.log(`✅ [PASS] ${name}: ${url}`);
      return true;
    } else {
      testResults.failed.push({ name, url, error: `Expected ${expectedStatus}, got ${response.status}` });
      console.log(`❌ [FAIL] ${name}: ${url} - Expected ${expectedStatus}, got ${response.status}`);
      return false;
    }
  } catch (error) {
    testResults.failed.push({ name, url, error: error.message });
    console.log(`❌ [FAIL] ${name}: ${url} - ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log('\n========================================');
  console.log('  开始API接口测试');
  console.log('========================================\n');
  
  // Visual Model后端测试
  console.log('\n--- Visual Model后端测试 ---\n');
  await testAPI('健康检查', `${BASE_URL}/api/v1/health`);
  await testAPI('系统信息', `${BASE_URL}/api/stats`);
  await testAPI('AI历史', `${BASE_URL}/api/v1/ai/history`);
  await testAPI('规则列表', `${BASE_URL}/api/v1/admin/rules/list`);
  await testAPI('用户列表', `${BASE_URL}/api/v1/admin/users`);
  await testAPI('综测配置列表', `${BASE_URL}/api/v1/comprehensive-score/config/list`);
  
  // RAG后端测试
  console.log('\n--- RAG后端测试 ---\n');
  await testAPI('RAG健康检查', `${RAG_URL}/health`);
  await testAPI('RAG系统信息', `${RAG_URL}/api/v1/system/info`);
  await testAPI('向量数据库统计', `${RAG_URL}/api/v1/vector-db/stats`);
  await testAPI('提示词列表', `${RAG_URL}/api/v1/prompts`);
  
  // AI对话测试
  console.log('\n--- AI对话测试 ---\n');
  await testPostAPI('AI对话', `${RAG_URL}/api/v1/chat`, {
    message: '测试消息',
    conversation_id: 'test'
  });
  
  console.log('\n========================================');
  console.log('  测试结果汇总');
  console.log('========================================\n');
  
  console.log(`总计测试: ${testResults.total}`);
  console.log(`通过: ${testResults.passed.length} ✅`);
  console.log(`失败: ${testResults.failed.length} ❌`);
  
  if (testResults.failed.length > 0) {
    console.log('\n失败的测试:');
    testResults.failed.forEach(test => {
      console.log(`  - ${test.name}: ${test.url}`);
      console.log(`    错误: ${test.error}`);
    });
  }
  
  console.log('\n');
  
  return testResults.failed.length === 0;
}

runTests().then(success => {
  process.exit(success ? 0 : 1);
}).catch(error => {
  console.error('测试执行失败:', error);
  process.exit(1);
});
