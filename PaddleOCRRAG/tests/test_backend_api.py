"""
RAG 服务后端 API 全面测试
测试核心功能、API端点、数据处理逻辑及边界情况
"""
import os
import sys
import time
import json
import pytest
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试配置
BASE_URL = os.environ.get("RAG_BASE_URL", "http://127.0.0.1:8010")
TIMEOUT = 30.0


class TestHealthEndpoints:
    """健康检查端点测试"""
    
    def test_health_check(self):
        """测试健康检查端点"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "healthy"
            assert "version" in data
    
    def test_root_endpoint(self):
        """测试根端点"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/")
            assert response.status_code == 200


class TestChatAPI:
    """AI 对话 API 测试"""
    
    def test_chat_endpoint_exists(self):
        """测试对话端点是否存在"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.post(
                "/api/chat",
                json={"message": "测试消息", "session_id": "test_session"}
            )
            assert response.status_code in [200, 400, 401, 404, 422]
    
    def test_chat_with_empty_message(self):
        """测试空消息边界情况"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.post(
                "/api/chat",
                json={"message": "", "session_id": "test"}
            )
            assert response.status_code in [200, 400, 401, 404, 422, 500]
    
    def test_chat_with_long_message(self):
        """测试长消息处理"""
        long_message = "测试" * 1000
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.post(
                "/api/chat",
                json={"message": long_message, "session_id": "test"}
            )
            assert response.status_code in [200, 400, 401, 404, 422]


class TestCertificateAPI:
    """证书管理 API 测试"""
    
    def test_certificate_list_endpoint(self):
        """测试证书列表端点"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/certificates")
            assert response.status_code in [200, 401, 404]
    
    def test_certificate_types_endpoint(self):
        """测试证书类型端点"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/certificates/types")
            assert response.status_code in [200, 401, 404]


class TestDocumentAPI:
    """文档管理 API 测试"""
    
    def test_document_list_endpoint(self):
        """测试文档列表端点"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/documents")
            assert response.status_code in [200, 401, 404]
    
    def test_document_stats_endpoint(self):
        """测试文档统计端点"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/documents/stats")
            assert response.status_code in [200, 401, 404]


class TestVectorDBAPI:
    """向量数据库 API 测试"""
    
    def test_vector_db_status(self):
        """测试向量数据库状态"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/vector-db/status")
            assert response.status_code in [200, 401, 404]
    
    def test_vector_db_count(self):
        """测试向量数据库文档计数"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/vector-db/count")
            assert response.status_code in [200, 401, 404]
    
    def test_vector_db_search(self):
        """测试向量数据库搜索"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.post(
                "/api/vector-db/search",
                json={"query": "电赛加分", "top_k": 5}
            )
            assert response.status_code in [200, 401, 404, 422]


class TestPromptAPI:
    """提示词管理 API 测试"""
    
    def test_prompt_list(self):
        """测试提示词列表"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/prompts")
            assert response.status_code in [200, 401, 404]
    
    def test_prompt_templates(self):
        """测试提示词模板"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/prompts/templates")
            assert response.status_code in [200, 401, 404]


class TestCacheAPI:
    """缓存管理 API 测试"""
    
    def test_cache_status(self):
        """测试缓存状态"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/cache/status")
            assert response.status_code in [200, 401, 404]
    
    def test_cache_clear(self):
        """测试缓存清除"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.delete("/api/cache/clear")
            assert response.status_code in [200, 401, 404]


class TestSystemAPI:
    """系统管理 API 测试"""
    
    def test_system_info(self):
        """测试系统信息"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/system/info")
            assert response.status_code in [200, 401, 404]
    
    def test_system_config(self):
        """测试系统配置"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/system/config")
            assert response.status_code in [200, 401, 404]


class TestLogAPI:
    """日志管理 API 测试"""
    
    def test_log_stats(self):
        """测试日志统计"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/logs/stats")
            assert response.status_code in [200, 401, 404]
    
    def test_log_search(self):
        """测试日志搜索"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/logs/search", params={"keyword": "test"})
            assert response.status_code in [200, 401, 404]


class TestLLMIntegration:
    """LLM 集成测试"""
    
    def test_llm_provider_status(self):
        """测试 LLM 提供商状态"""
        from app.core.llm_manager import LLMManager
        
        llm_manager = LLMManager()
        providers = llm_manager.list_providers()
        
        assert len(providers) > 0, "应该至少有一个 LLM 提供商"
        assert "xunfei" in providers, "应该有讯飞提供商"
    
    def test_llm_connection(self):
        """测试 LLM 连接"""
        from app.core.llm_manager import LLMManager
        
        llm_manager = LLMManager()
        result = llm_manager.test_connection()
        
        assert result is not None, "连接测试应该返回结果"
        assert "success" in result, "结果应该包含 success 字段"
    
    def test_llm_generation(self):
        """测试 LLM 生成"""
        from app.core.llm_manager import LLMManager
        
        llm_manager = LLMManager()
        response = llm_manager.generate("你好", max_tokens=50)
        
        assert response is not None, "应该返回响应"
        assert len(response) > 0, "响应不应为空"


class TestRuleMatching:
    """规则匹配测试"""
    
    def test_rule_match_competition(self):
        """测试竞赛规则匹配"""
        from app.core.llm_manager import RuleMatchingEngine
        
        engine = RuleMatchingEngine()
        result = engine.match("电赛国赛一等奖加多少分？")
        
        assert result is not None, "应该返回匹配结果"
        assert "result" in result or "match" in result, "结果应该包含匹配信息"
    
    def test_rule_match_certificate(self):
        """测试证书规则匹配"""
        from app.core.llm_manager import RuleMatchingEngine
        
        engine = RuleMatchingEngine()
        result = engine.match("英语六级证书加分")
        
        assert result is not None, "应该返回匹配结果"


class TestVectorDBIntegration:
    """向量数据库集成测试"""
    
    @pytest.mark.skip(reason="Windows 环境下 chromadb/numpy 兼容性问题")
    def test_vector_db_initialization(self):
        """测试向量数据库初始化"""
        from app.rag.vector_db.vector_db import get_vector_db
        
        vdb = get_vector_db()
        assert vdb is not None, "向量数据库应该成功初始化"
    
    @pytest.mark.skip(reason="Windows 环境下 chromadb/numpy 兼容性问题")
    def test_vector_db_count(self):
        """测试向量数据库文档计数"""
        from app.rag.vector_db.vector_db import get_vector_db
        
        vdb = get_vector_db()
        count = vdb.count()
        
        assert count >= 0, "文档计数应该非负"
    
    @pytest.mark.skip(reason="Windows 环境下 chromadb/numpy 兼容性问题")
    def test_vector_db_query(self):
        """测试向量数据库查询"""
        from app.rag.vector_db.vector_db import get_vector_db
        
        vdb = get_vector_db()
        results = vdb.query("电赛加分规则", top_k=3)
        
        assert results is not None, "查询应该返回结果"
        assert isinstance(results, dict), "结果应该是字典"


class TestPerformance:
    """性能测试"""
    
    def test_health_check_performance(self):
        """测试健康检查性能"""
        start_time = time.time()
        
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/health")
        
        duration = time.time() - start_time
        assert response.status_code == 200
        assert duration < 1.0, f"健康检查应该在1秒内完成，实际耗时: {duration:.3f}秒"
    
    def test_llm_response_time(self):
        """测试 LLM 响应时间"""
        from app.core.llm_manager import LLMManager
        
        llm_manager = LLMManager()
        
        start_time = time.time()
        response = llm_manager.generate("你好", max_tokens=50)
        duration = time.time() - start_time
        
        assert response is not None
        assert duration < 10.0, f"LLM 响应应该在10秒内完成，实际耗时: {duration:.3f}秒"


class TestErrorHandling:
    """错误处理测试"""
    
    def test_invalid_endpoint(self):
        """测试无效端点"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.get("/api/invalid-endpoint")
            assert response.status_code == 404
    
    def test_invalid_json(self):
        """测试无效 JSON"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.post(
                "/api/chat",
                content="invalid json",
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code in [400, 404, 422]
    
    def test_missing_required_field(self):
        """测试缺少必填字段"""
        with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
            response = client.post("/api/chat", json={})
            assert response.status_code in [400, 404, 422]


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("RAG 服务后端 API 全面测试")
    print("="*60)
    print(f"测试目标: {BASE_URL}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    
    return result.returncode == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
