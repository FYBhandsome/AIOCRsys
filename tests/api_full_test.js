/**
 * 完整API自动化测试脚本
 * 测试所有后端API端点
 * 
 * Visual Model后端: http://localhost:8001/api/v1
 * RAG后端: http://localhost:8010
 */

const VISUAL_MODEL_BASE = 'http://localhost:8001/api/v1';
const RAG_BASE = 'http://localhost:8010';

const testResults = {
  total: 0,
  passed: 0,
  failed: 0,
  skipped: 0,
  details: {
    passed: [],
    failed: [],
    skipped: []
  },
  startTime: null,
  endTime: null
};

let authToken = null;

function log(message, type = 'info') {
  const timestamp = new Date().toISOString();
  const symbols = {
    info: 'ℹ️',
    success: '✅',
    error: '❌',
    warning: '⚠️',
    skip: '⏭️'
  };
  console.log(`${symbols[type] || 'ℹ️'} [${timestamp}] ${message}`);
}

async function fetchWithTimeout(url, options = {}, timeout = 10000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

async function testEndpoint(name, url, options = {}, expectedStatus = 200) {
  testResults.total++;
  const startTime = Date.now();
  
  try {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };
    
    if (authToken && !options.skipAuth) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const response = await fetchWithTimeout(url, {
      ...options,
      headers
    });
    
    const duration = Date.now() - startTime;
    const status = response.status;
    
    let data = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      try {
        data = await response.json();
      } catch (e) {
        data = { raw: await response.text() };
      }
    }
    
    if (status === expectedStatus || (expectedStatus === 'any' && status < 500)) {
      testResults.passed++;
      testResults.details.passed.push({
        name,
        url,
        status,
        duration,
        method: options.method || 'GET'
      });
      log(`${name} [${options.method || 'GET'} ${url}] - ${status} (${duration}ms)`, 'success');
      return { success: true, status, data, duration };
    } else {
      testResults.failed++;
      testResults.details.failed.push({
        name,
        url,
        expectedStatus,
        actualStatus: status,
        error: `Expected status ${expectedStatus}, got ${status}`,
        duration,
        method: options.method || 'GET'
      });
      log(`${name} [${options.method || 'GET'} ${url}] - Expected ${expectedStatus}, got ${status}`, 'error');
      return { success: false, status, data, duration };
    }
  } catch (error) {
    const duration = Date.now() - startTime;
    testResults.failed++;
    testResults.details.failed.push({
      name,
      url,
      error: error.message,
      duration,
      method: options.method || 'GET'
    });
    log(`${name} [${options.method || 'GET'} ${url}] - ${error.message}`, 'error');
    return { success: false, error: error.message, duration };
  }
}

function skipTest(name, url, reason) {
  testResults.total++;
  testResults.skipped++;
  testResults.details.skipped.push({ name, url, reason });
  log(`${name} [${url}] - Skipped: ${reason}`, 'skip');
}

async function testHealthEndpoints() {
  log('\n========== 健康检查端点测试 ==========', 'info');
  
  await testEndpoint('Visual Model 健康检查', `${VISUAL_MODEL_BASE}/health`);
  await testEndpoint('RAG 健康检查', `${RAG_BASE}/health`);
  await testEndpoint('RAG 系统健康检查', `${RAG_BASE}/api/v1/system/health`);
}

async function testAuthAPI() {
  log('\n========== 认证API测试 ==========', 'info');
  
  const loginResult = await testEndpoint('管理员登录', `${VISUAL_MODEL_BASE}/auth/login`, {
    method: 'POST',
    body: JSON.stringify({
      username: 'admin',
      password: 'admin123'
    })
  }, 'any');
  
  if (loginResult.success && loginResult.data && loginResult.data.access_token) {
    authToken = loginResult.data.access_token;
    log('已获取认证Token', 'info');
  } else {
    log('登录失败，后续测试将跳过认证', 'warning');
  }
  
  if (authToken) {
    await testEndpoint('获取当前用户信息', `${VISUAL_MODEL_BASE}/auth/me`);
  } else {
    skipTest('获取当前用户信息', `${VISUAL_MODEL_BASE}/auth/me`, '需要认证Token');
  }
  
  await testEndpoint('用户登出', `${VISUAL_MODEL_BASE}/auth/logout`, {
    method: 'POST'
  }, 'any');
  
  await testEndpoint('学生登录', `${VISUAL_MODEL_BASE}/auth/login`, {
    method: 'POST',
    body: JSON.stringify({
      username: 'student',
      password: 'student123'
    })
  }, 'any');
  
  await testEndpoint('教师登录', `${VISUAL_MODEL_BASE}/auth/login`, {
    method: 'POST',
    body: JSON.stringify({
      username: 'teacher',
      password: 'teacher123'
    })
  }, 'any');
}

async function testStudentAPI() {
  log('\n========== 学生API测试 ==========', 'info');
  
  await testEndpoint('获取成绩摘要', `${VISUAL_MODEL_BASE}/student/scores/summary`, {}, 'any');
  await testEndpoint('获取成绩详情', `${VISUAL_MODEL_BASE}/student/scores/detail`, {}, 'any');
  await testEndpoint('获取上传历史', `${VISUAL_MODEL_BASE}/student/uploads`, {}, 'any');
  await testEndpoint('获取证书列表', `${VISUAL_MODEL_BASE}/student/certificates`, {}, 'any');
  await testEndpoint('获取综合分析', `${VISUAL_MODEL_BASE}/student/comprehensive/analysis`, {}, 'any');
  await testEndpoint('获取成绩趋势', `${VISUAL_MODEL_BASE}/student/scores/trend`, {}, 'any');
}

async function testTeacherAPI() {
  log('\n========== 教师API测试 ==========', 'info');
  
  await testEndpoint('获取班级列表', `${VISUAL_MODEL_BASE}/teacher/classes`, {}, 'any');
  await testEndpoint('获取学生列表', `${VISUAL_MODEL_BASE}/teacher/students`, {}, 'any');
  await testEndpoint('成绩分析', `${VISUAL_MODEL_BASE}/teacher/scores/analysis`, {}, 'any');
  await testEndpoint('班级统计', `${VISUAL_MODEL_BASE}/teacher/classes/stats`, {}, 'any');
  await testEndpoint('班级排名', `${VISUAL_MODEL_BASE}/teacher/classes/ranking`, {}, 'any');
}

async function testAdminAPI() {
  log('\n========== 管理员API测试 ==========', 'info');
  
  await testEndpoint('获取用户列表', `${VISUAL_MODEL_BASE}/admin/users`, {}, 'any');
  await testEndpoint('获取规则文档列表', `${VISUAL_MODEL_BASE}/admin/rules/list`, {}, 'any');
  await testEndpoint('获取系统设置', `${VISUAL_MODEL_BASE}/admin/settings`, {}, 'any');
  await testEndpoint('获取AI配置', `${VISUAL_MODEL_BASE}/admin/ai/config`, {}, 'any');
  await testEndpoint('获取Prompt配置', `${VISUAL_MODEL_BASE}/admin/prompts`, {}, 'any');
  await testEndpoint('获取向量数据库统计', `${VISUAL_MODEL_BASE}/admin/vector-db/stats`, {}, 'any');
  await testEndpoint('获取RAG统计', `${VISUAL_MODEL_BASE}/admin/rag/stats`, {}, 'any');
  await testEndpoint('RAG健康检查', `${VISUAL_MODEL_BASE}/admin/rag/health`, {}, 'any');
  
  await testEndpoint('获取综测配置列表', `${VISUAL_MODEL_BASE}/admin/comprehensive-score-config`, {}, 'any');
  await testEndpoint('获取默认综测配置', `${VISUAL_MODEL_BASE}/admin/comprehensive-score-config/default`, {}, 'any');
  await testEndpoint('获取可用学业成绩字段', `${VISUAL_MODEL_BASE}/admin/comprehensive-score-config/fields`, {}, 'any');
}

async function testFileManagementAPI() {
  log('\n========== 文件管理API测试 ==========', 'info');
  
  await testEndpoint('获取文件分类', `${VISUAL_MODEL_BASE}/file/categories`);
  await testEndpoint('获取文件列表', `${VISUAL_MODEL_BASE}/file/list`, {}, 'any');
  await testEndpoint('获取下载历史', `${VISUAL_MODEL_BASE}/file/download-history`, {}, 'any');
}

async function testRAGChatAPI() {
  log('\n========== RAG聊天API测试 ==========', 'info');
  
  await testEndpoint('发送聊天消息', `${RAG_BASE}/api/v1/chat`, {
    method: 'POST',
    body: JSON.stringify({
      message: '你好，请介绍一下综测计算规则',
      use_rag: true
    })
  }, 'any');
  
  await testEndpoint('获取聊天缓存统计', `${RAG_BASE}/api/v1/chat/cache/stats`);
}

async function testRAGDocumentAPI() {
  log('\n========== RAG文档管理API测试 ==========', 'info');
  
  await testEndpoint('获取文档列表', `${RAG_BASE}/api/v1/documents`);
  await testEndpoint('文档分析概览', `${RAG_BASE}/api/v1/documents/analyze/overview`, {}, 'any');
  await testEndpoint('获取文档规则', `${RAG_BASE}/api/v1/documents/analyze/rules`, {}, 'any');
  await testEndpoint('获取综测比例数据', `${RAG_BASE}/api/v1/documents/analyze/ratios`, {}, 'any');
  await testEndpoint('获取文档分析说明', `${RAG_BASE}/api/v1/documents/analyze/description`, {}, 'any');
}

async function testRAGSystemAPI() {
  log('\n========== RAG系统管理API测试 ==========', 'info');
  
  await testEndpoint('获取系统信息', `${RAG_BASE}/api/v1/system/info`);
  await testEndpoint('获取系统配置', `${RAG_BASE}/api/v1/system/config`);
  await testEndpoint('获取LLM配置', `${RAG_BASE}/api/v1/system/llm/config`);
  await testEndpoint('获取模型信息', `${RAG_BASE}/api/v1/system/model-info`);
  await testEndpoint('获取向量数据库统计', `${RAG_BASE}/api/v1/system/vector_db/stats`);
}

async function testRAGVectorDBAPI() {
  log('\n========== RAG向量数据库API测试 ==========', 'info');
  
  await testEndpoint('向量数据库统计', `${RAG_BASE}/api/v1/vector-db/stats`);
  await testEndpoint('向量数据库健康检查', `${RAG_BASE}/api/v1/vector-db/health`);
  await testEndpoint('向量数据库集合列表', `${RAG_BASE}/api/v1/vector-db/collections`);
}

async function testRAGPromptAPI() {
  log('\n========== RAG Prompt API测试 ==========', 'info');
  
  await testEndpoint('获取Prompt列表', `${RAG_BASE}/api/v1/prompts`);
}

async function testRAGCacheAPI() {
  log('\n========== RAG缓存API测试 ==========', 'info');
  
  await testEndpoint('获取缓存统计', `${RAG_BASE}/api/v1/cache/stats`);
}

async function testRAGLogAPI() {
  log('\n========== RAG日志API测试 ==========', 'info');
  
  await testEndpoint('获取日志统计', `${RAG_BASE}/api/v1/logs/stats`, {}, 'any');
}

async function testRAGCertificateAPI() {
  log('\n========== RAG证书API测试 ==========', 'info');
  
  await testEndpoint('证书计算', `${RAG_BASE}/api/v1/certificate/calculate`, {
    method: 'POST',
    body: JSON.stringify({
      certificate_text: '获得全国大学生数学建模竞赛一等奖',
      certificate_info: {}
    })
  }, 'any');
}

function generateReport() {
  testResults.endTime = new Date();
  const duration = (testResults.endTime - testResults.startTime) / 1000;
  
  const report = {
    summary: {
      total: testResults.total,
      passed: testResults.passed,
      failed: testResults.failed,
      skipped: testResults.skipped,
      passRate: testResults.total > 0 
        ? ((testResults.passed / testResults.total) * 100).toFixed(2) + '%' 
        : '0%',
      duration: duration.toFixed(2) + 's',
      startTime: testResults.startTime.toISOString(),
      endTime: testResults.endTime.toISOString()
    },
    details: testResults.details
  };
  
  return report;
}

function printSummary() {
  const report = generateReport();
  
  console.log('\n');
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║                    测试结果汇总                              ║');
  console.log('╠════════════════════════════════════════════════════════════╣');
  console.log(`║  总测试数: ${report.summary.total.toString().padEnd(47)}║`);
  console.log(`║  通过: ${report.summary.passed.toString().padEnd(51)}║`);
  console.log(`║  失败: ${report.summary.failed.toString().padEnd(51)}║`);
  console.log(`║  跳过: ${report.summary.skipped.toString().padEnd(51)}║`);
  console.log(`║  通过率: ${report.summary.passRate.padEnd(49)}║`);
  console.log(`║  耗时: ${report.summary.duration.padEnd(51)}║`);
  console.log('╚════════════════════════════════════════════════════════════╝');
  
  if (testResults.details.failed.length > 0) {
    console.log('\n❌ 失败的测试:');
    testResults.details.failed.forEach((test, index) => {
      console.log(`  ${index + 1}. ${test.name}`);
      console.log(`     URL: ${test.url}`);
      console.log(`     方法: ${test.method || 'GET'}`);
      if (test.error) {
        console.log(`     错误: ${test.error}`);
      }
      if (test.actualStatus) {
        console.log(`     状态码: ${test.actualStatus} (期望: ${test.expectedStatus})`);
      }
    });
  }
  
  if (testResults.details.skipped.length > 0) {
    console.log('\n⏭️ 跳过的测试:');
    testResults.details.skipped.forEach((test, index) => {
      console.log(`  ${index + 1}. ${test.name} - ${test.reason}`);
    });
  }
  
  return report;
}

function saveReportToFile(report) {
  const fs = require('fs');
  const path = require('path');
  
  const reportDir = path.join(__dirname, 'reports');
  if (!fs.existsSync(reportDir)) {
    fs.mkdirSync(reportDir, { recursive: true });
  }
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const reportPath = path.join(reportDir, `api_test_report_${timestamp}.json`);
  
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf-8');
  log(`测试报告已保存到: ${reportPath}`, 'info');
  
  return reportPath;
}

async function runAllTests() {
  testResults.startTime = new Date();
  
  console.log('\n');
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║           完整API自动化测试 - 开始执行                       ║');
  console.log('╠════════════════════════════════════════════════════════════╣');
  console.log(`║  Visual Model后端: ${VISUAL_MODEL_BASE.padEnd(36)}║`);
  console.log(`║  RAG后端: ${RAG_BASE.padEnd(47)}║`);
  console.log(`║  开始时间: ${testResults.startTime.toISOString().padEnd(44)}║`);
  console.log('╚════════════════════════════════════════════════════════════╝');
  
  try {
    await testHealthEndpoints();
    await testAuthAPI();
    await testStudentAPI();
    await testTeacherAPI();
    await testAdminAPI();
    await testFileManagementAPI();
    await testRAGChatAPI();
    await testRAGDocumentAPI();
    await testRAGSystemAPI();
    await testRAGVectorDBAPI();
    await testRAGPromptAPI();
    await testRAGCacheAPI();
    await testRAGLogAPI();
    await testRAGCertificateAPI();
  } catch (error) {
    log(`测试执行出错: ${error.message}`, 'error');
    console.error(error);
  }
  
  const report = printSummary();
  
  try {
    const reportPath = saveReportToFile(report);
    console.log(`\n📄 JSON测试报告: ${reportPath}`);
  } catch (error) {
    log(`保存报告失败: ${error.message}`, 'warning');
  }
  
  console.log('\n测试完成！\n');
  
  return testResults.failed === 0;
}

runAllTests()
  .then(success => {
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('测试执行失败:', error);
    process.exit(1);
  });
