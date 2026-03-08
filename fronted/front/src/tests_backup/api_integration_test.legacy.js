/**
 * 前端API集成测试脚本
 * 测试所有API端点的请求和响应
 */

const BASE_URL = 'http://localhost:8010/api';
const RAG_URL = 'http://localhost:8001/api/v1/api';

let authToken = null;
let testResults = {
    total: 0,
    passed: 0,
    failed: 0,
    errors: []
};

function log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = {
        'info': '[INFO]',
        'success': '[SUCCESS]',
        'error': '[ERROR]',
        'warning': '[WARNING]'
    }[type] || '[INFO]';
    
    console.log(`${timestamp} ${prefix} ${message}`);
}

async function request(method, url, data = null, headers = {}) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...headers
        }
    };
    
    if (authToken) {
        options.headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        const responseText = await response.text();
        let responseData;
        
        try {
            responseData = JSON.parse(responseText);
        } catch {
            responseData = responseText;
        }
        
        return {
            status: response.status,
            ok: response.ok,
            data: responseData,
            headers: Object.fromEntries(response.headers.entries())
        };
    } catch (error) {
        return {
            status: 0,
            ok: false,
            error: error.message
        };
    }
}

function assert(condition, testName, details = '') {
    testResults.total++;
    if (condition) {
        testResults.passed++;
        log(`${testName} - 通过 ${details}`, 'success');
    } else {
        testResults.failed++;
        testResults.errors.push({ test: testName, details });
        log(`${testName} - 失败 ${details}`, 'error');
    }
}

async function testAuthAPI() {
    log('========== 认证API测试 ==========');
    
    log('测试: 用户登录');
    const loginResult = await request('POST', `${BASE_URL}/auth/login`, {
        username: 'admin',
        password: 'admin123'
    });
    
    log(`请求参数: {"username": "admin", "password": "admin123"}`);
    log(`响应状态码: ${loginResult.status}`);
    log(`响应数据: ${JSON.stringify(loginResult.data).substring(0, 200)}`);
    
    if (loginResult.ok && loginResult.data.access_token) {
        authToken = loginResult.data.access_token;
        assert(true, '用户登录', `获取到令牌`);
    } else {
        assert(false, '用户登录', `登录失败: ${JSON.stringify(loginResult.data)}`);
    }
    
    log('测试: 获取当前用户信息');
    const meResult = await request('GET', `${BASE_URL}/auth/me`);
    log(`响应状态码: ${meResult.status}`);
    log(`响应数据: ${JSON.stringify(meResult.data).substring(0, 200)}`);
    assert(meResult.ok, '获取当前用户信息', JSON.stringify(meResult.data).substring(0, 100));
    
    log('测试: 登录错误密码');
    const wrongLoginResult = await request('POST', `${BASE_URL}/auth/login`, {
        username: 'admin',
        password: 'wrongpassword'
    });
    log(`响应状态码: ${wrongLoginResult.status}`);
    assert(wrongLoginResult.status === 401, '登录错误密码应返回401');
    
    log('测试: 无令牌访问受保护端点');
    const tempToken = authToken;
    authToken = null;
    const noAuthResult = await request('GET', `${BASE_URL}/auth/me`);
    authToken = tempToken;
    log(`响应状态码: ${noAuthResult.status}`);
    assert(noAuthResult.status === 401 || noAuthResult.status === 403, '无令牌应返回401或403');
}

async function testStudentAPI() {
    log('========== 学生API测试 ==========');
    
    log('测试: 获取学生个人信息');
    const profileResult = await request('GET', `${BASE_URL}/student/profile`);
    log(`响应状态码: ${profileResult.status}`);
    log(`响应数据: ${JSON.stringify(profileResult.data).substring(0, 200)}`);
    assert(profileResult.ok || profileResult.status === 404, '获取学生个人信息');
    
    log('测试: 获取学生成绩');
    const scoresResult = await request('GET', `${BASE_URL}/student/scores`);
    log(`响应状态码: ${scoresResult.status}`);
    assert(scoresResult.ok || scoresResult.status === 404, '获取学生成绩');
    
    log('测试: 获取学生证书列表');
    const certsResult = await request('GET', `${BASE_URL}/student/certificates`);
    log(`响应状态码: ${certsResult.status}`);
    assert(certsResult.ok || certsResult.status === 404, '获取学生证书列表');
    
    log('测试: 获取综测成绩');
    const compScoreResult = await request('GET', `${BASE_URL}/student/comprehensive-score`);
    log(`响应状态码: ${compScoreResult.status}`);
    assert(compScoreResult.ok || compScoreResult.status === 404, '获取综测成绩');
}

async function testTeacherAPI() {
    log('========== 教师API测试 ==========');
    
    log('测试: 获取教师班级列表');
    const classesResult = await request('GET', `${BASE_URL}/teacher/classes`);
    log(`响应状态码: ${classesResult.status}`);
    log(`响应数据: ${JSON.stringify(classesResult.data).substring(0, 200)}`);
    assert(classesResult.ok, '获取教师班级列表');
    
    log('测试: 获取班级成绩统计');
    const statsResult = await request('GET', `${BASE_URL}/teacher/scores/stats/test_class_id`);
    log(`响应状态码: ${statsResult.status}`);
    assert(statsResult.ok || statsResult.status === 404, '获取班级成绩统计');
    
    log('测试: 获取班级排名');
    const rankingResult = await request('GET', `${BASE_URL}/teacher/scores/ranking/test_class_id`);
    log(`响应状态码: ${rankingResult.status}`);
    assert(rankingResult.ok || rankingResult.status === 404, '获取班级排名');
    
    log('测试: 获取待审核证书');
    const pendingResult = await request('GET', `${BASE_URL}/teacher/certificates/pending`);
    log(`响应状态码: ${pendingResult.status}`);
    assert(pendingResult.ok || pendingResult.status === 404, '获取待审核证书');
}

async function testAdminAPI() {
    log('========== 管理员API测试 ==========');
    
    log('测试: 获取用户列表');
    const usersResult = await request('GET', `${BASE_URL}/admin/users`);
    log(`响应状态码: ${usersResult.status}`);
    log(`响应数据: ${JSON.stringify(usersResult.data).substring(0, 200)}`);
    assert(usersResult.ok, '获取用户列表');
    
    log('测试: 获取班级列表');
    const classesResult = await request('GET', `${BASE_URL}/admin/classes`);
    log(`响应状态码: ${classesResult.status}`);
    assert(classesResult.ok, '获取班级列表');
    
    log('测试: 获取系统统计');
    const statsResult = await request('GET', `${BASE_URL}/admin/system/stats`);
    log(`响应状态码: ${statsResult.status}`);
    assert(statsResult.ok || statsResult.status === 404, '获取系统统计');
}

async function testAIAPI() {
    log('========== AI助手API测试 ==========');
    
    log('测试: AI对话');
    const chatResult = await request('POST', `${BASE_URL}/ai/chat`, {
        message: '省级竞赛加多少分？',
        use_rag: true
    });
    log(`请求参数: {"message": "省级竞赛加多少分？", "use_rag": true}`);
    log(`响应状态码: ${chatResult.status}`);
    log(`响应数据: ${JSON.stringify(chatResult.data).substring(0, 300)}`);
    assert(chatResult.ok, 'AI对话', JSON.stringify(chatResult.data).substring(0, 100));
    
    log('测试: AI助手消息接口');
    const assistantResult = await request('POST', `${BASE_URL}/ai/assistant/message`, {
        question: '英语四级可以加多少分？'
    });
    log(`响应状态码: ${assistantResult.status}`);
    assert(assistantResult.ok, 'AI助手消息接口');
    
    log('测试: 获取建议问题');
    const suggestionsResult = await request('GET', `${BASE_URL}/ai/suggestions`);
    log(`响应状态码: ${suggestionsResult.status}`);
    assert(suggestionsResult.ok, '获取建议问题');
    
    log('测试: 空消息验证');
    const emptyMsgResult = await request('POST', `${BASE_URL}/ai/chat`, {
        message: ''
    });
    log(`响应状态码: ${emptyMsgResult.status}`);
    assert(emptyMsgResult.status === 422, '空消息应返回422');
}

async function testRAGAPI() {
    log('========== RAG系统API测试 ==========');
    
    log('测试: RAG聊天');
    const chatResult = await request('POST', `${RAG_URL}/chat`, {
        message: '综测加分规则是什么？'
    });
    log(`响应状态码: ${chatResult.status}`);
    assert(chatResult.ok || chatResult.status === 0, 'RAG聊天');
    
    log('测试: 计算证书加分');
    const certResult = await request('POST', `${RAG_URL}/certificate/calculate`, {
        certificate_name: '蓝桥杯',
        level: '省级',
        award: '一等奖'
    });
    log(`响应状态码: ${certResult.status}`);
    assert(certResult.ok || certResult.status === 422, '计算证书加分');
    
    log('测试: 获取文档列表');
    const docsResult = await request('GET', `${RAG_URL}/documents`);
    log(`响应状态码: ${docsResult.status}`);
    assert(docsResult.ok || docsResult.status === 0, '获取文档列表');
    
    log('测试: 系统健康检查');
    const healthResult = await request('GET', `${RAG_URL}/system/health`);
    log(`响应状态码: ${healthResult.status}`);
    assert(healthResult.ok || healthResult.status === 0, '系统健康检查');
}

async function runAllTests() {
    log('========================================');
    log('开始执行前端API集成测试');
    log(`测试时间: ${new Date().toLocaleString()}`);
    log('========================================');
    
    try {
        await testAuthAPI();
        await testStudentAPI();
        await testTeacherAPI();
        await testAdminAPI();
        await testAIAPI();
        await testRAGAPI();
    } catch (error) {
        log(`测试执行出错: ${error.message}`, 'error');
    }
    
    log('========================================');
    log('测试执行完成');
    log(`总计: ${testResults.total} 测试`);
    log(`通过: ${testResults.passed}`, 'success');
    log(`失败: ${testResults.failed}`, testResults.failed > 0 ? 'error' : 'info');
    log('========================================');
    
    if (testResults.errors.length > 0) {
        log('失败详情:', 'error');
        testResults.errors.forEach((err, idx) => {
            log(`  ${idx + 1}. ${err.test}: ${err.details}`, 'error');
        });
    }
    
    return testResults;
}

if (typeof window !== 'undefined') {
    window.runAPITests = runAllTests;
    log('测试脚本已加载，调用 window.runAPITests() 执行测试');
} else {
    runAllTests();
}

export { runAllTests, testResults };
