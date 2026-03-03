/**
 * API接口测试文件
 * 测试前端与后端API的集成
 */

import { authAPI, studentAPI, teacherAPI, adminAPI, ragAPI } from '@/services/api'

// 测试配置
const TEST_CONFIG = {
  baseUrl: 'http://localhost:8001',
  ragUrl: 'http://localhost:8000',
  timeout: 30000
}

// 测试用户
const TEST_USERS = {
  admin: { username: 'dev_admin', password: 'dev123456' },
  teacher: { username: 'dev_teacher', password: 'dev123456' },
  student: { username: 'dev_student', password: 'dev123456' }
}

// 测试结果收集
const testResults = {
  passed: 0,
  failed: 0,
  errors: []
}

// 测试工具函数
function logTest(name, passed, error = null) {
  if (passed) {
    console.log(`✅ ${name}`)
    testResults.passed++
  } else {
    console.error(`❌ ${name}: ${error}`)
    testResults.failed++
    testResults.errors.push({ name, error: error?.message || error })
  }
}

// 1. 认证API测试
async function testAuthAPI() {
  console.log('\n=== 认证API测试 ===')
  
  // 1.1 登录测试
  try {
    const result = await authAPI.login(TEST_USERS.admin.username, TEST_USERS.admin.password)
    logTest('管理员登录', result && result.token)
  } catch (e) {
    logTest('管理员登录', false, e)
  }
  
  // 1.2 获取用户信息
  try {
    const result = await authAPI.getUserInfo()
    logTest('获取用户信息', result && result.username)
  } catch (e) {
    logTest('获取用户信息', false, e)
  }
}

// 2. 学生API测试
async function testStudentAPI() {
  console.log('\n=== 学生API测试 ===')
  
  // 2.1 获取成绩摘要
  try {
    const result = await studentAPI.getScoresSummary()
    logTest('获取成绩摘要', result !== undefined)
  } catch (e) {
    logTest('获取成绩摘要', false, e)
  }
  
  // 2.2 获取上传历史
  try {
    const result = await studentAPI.getUploadHistory()
    logTest('获取上传历史', result !== undefined)
  } catch (e) {
    logTest('获取上传历史', false, e)
  }
  
  // 2.3 获取材料列表
  try {
    const result = await studentAPI.getMaterials()
    logTest('获取材料列表', result !== undefined)
  } catch (e) {
    logTest('获取材料列表', false, e)
  }
}

// 3. 教师API测试
async function testTeacherAPI() {
  console.log('\n=== 教师API测试 ===')
  
  // 3.1 获取学生列表
  try {
    const result = await teacherAPI.getStudents()
    logTest('获取学生列表', result !== undefined)
  } catch (e) {
    logTest('获取学生列表', false, e)
  }
  
  // 3.2 获取班级列表
  try {
    const result = await teacherAPI.getClasses()
    logTest('获取班级列表', result !== undefined)
  } catch (e) {
    logTest('获取班级列表', false, e)
  }
}

// 4. 管理员API测试
async function testAdminAPI() {
  console.log('\n=== 管理员API测试 ===')
  
  // 4.1 获取用户列表
  try {
    const result = await adminAPI.getUsers()
    logTest('获取用户列表', result !== undefined)
  } catch (e) {
    logTest('获取用户列表', false, e)
  }
  
  // 4.2 获取系统设置
  try {
    const result = await adminAPI.getSystemSettings()
    logTest('获取系统设置', result !== undefined)
  } catch (e) {
    logTest('获取系统设置', false, e)
  }
  
  // 4.3 获取规则文档列表
  try {
    const result = await adminAPI.getRuleDocuments()
    logTest('获取规则文档列表', result !== undefined)
  } catch (e) {
    logTest('获取规则文档列表', false, e)
  }
}

// 5. RAG API测试
async function testRagAPI() {
  console.log('\n=== RAG API测试 ===')
  
  // 5.1 AI对话测试
  try {
    const result = await ragAPI.chat('什么是综测？', [], true)
    logTest('AI对话测试', result && result.answer)
  } catch (e) {
    logTest('AI对话测试', false, e)
  }
  
  // 5.2 获取系统信息
  try {
    const result = await ragAPI.getSystemInfo()
    logTest('获取RAG系统信息', result !== undefined)
  } catch (e) {
    logTest('获取RAG系统信息', false, e)
  }
}

// 主测试函数
async function runAllTests() {
  console.log('========================================')
  console.log('开始执行API接口测试')
  console.log('========================================')
  
  const startTime = Date.now()
  
  try {
    await testAuthAPI()
    await testStudentAPI()
    await testTeacherAPI()
    await testAdminAPI()
    await testRagAPI()
  } catch (e) {
    console.error('测试执行错误:', e)
  }
  
  const duration = Date.now() - startTime
  
  console.log('\n========================================')
  console.log('测试结果汇总')
  console.log('========================================')
  console.log(`✅ 通过: ${testResults.passed}`)
  console.log(`❌ 失败: ${testResults.failed}`)
  console.log(`⏱️ 耗时: ${duration}ms`)
  console.log(`📊 通过率: ${((testResults.passed / (testResults.passed + testResults.failed)) * 100).toFixed(1)}%`)
  
  if (testResults.errors.length > 0) {
    console.log('\n错误详情:')
    testResults.errors.forEach((err, i) => {
      console.log(`${i + 1}. ${err.name}: ${err.error}`)
    })
  }
  
  return testResults
}

// 导出测试函数
export {
  runAllTests,
  testAuthAPI,
  testStudentAPI,
  testTeacherAPI,
  testAdminAPI,
  testRagAPI,
  testResults
}

// 如果直接运行此文件
if (typeof window !== 'undefined') {
  window.runApiTests = runAllTests
  console.log('测试函数已挂载到 window.runApiTests，可在控制台运行')
}
