"""
AI连接测试脚本
验证讯飞星火大模型的连接性
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config_manager import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def test_config_loaded():
    """测试配置是否正确加载"""
    print("\n" + "="*60)
    print("测试1: AI配置信息检查")
    print("="*60)
    
    print(f"\n  USE_XUNFEI_LLM: {settings.USE_XUNFEI_LLM}")
    
    api_key = settings.XUNFEI_API_KEY
    if api_key:
        masked_key = api_key[:10] + '*' * 20 + api_key[-10:] if len(api_key) > 30 else '*' * len(api_key)
        print(f"  XUNFEI_API_KEY: {masked_key}")
    else:
        print(f"  XUNFEI_API_KEY: 未配置")
    
    print(f"  XUNFEI_API_URL: {settings.XUNFEI_API_URL}")
    print(f"  XUNFEI_MODEL_ID: {settings.XUNFEI_MODEL_ID}")
    print(f"  XUNFEI_TEMPERATURE: {settings.XUNFEI_TEMPERATURE}")
    print(f"  XUNFEI_MAX_TOKENS: {settings.XUNFEI_MAX_TOKENS}")
    
    assert settings.USE_XUNFEI_LLM, "USE_XUNFEI_LLM 应该为 True"
    assert settings.XUNFEI_API_KEY, "XUNFEI_API_KEY 应该已配置"
    print("\n  ✅ 配置已正确加载")


def test_llm_manager():
    """测试LLM管理器初始化"""
    print("\n" + "="*60)
    print("测试2: LLM管理器初始化")
    print("="*60)
    
    from app.core.llm_manager import LLMManager
    
    llm_manager = LLMManager()
    
    print(f"\n  LLM管理器状态: 已初始化")
    
    providers = llm_manager.list_providers()
    print(f"  可用提供商: {providers}")
    assert len(providers) > 0, "应该至少有一个提供商"
    
    status = llm_manager.get_provider_status()
    print(f"  提供商状态: {status}")
    
    default_provider = llm_manager.get_default_provider()
    assert default_provider is not None, "应该有默认提供商"
    print(f"  默认提供商类型: {type(default_provider).__name__}")
    
    available = default_provider.is_available()
    print(f"  提供商可用: {'是' if available else '否'}")
    assert available, "提供商应该可用"
    print("\n  ✅ LLM管理器初始化成功")


def test_api_connection():
    """测试API连接"""
    print("\n" + "="*60)
    print("测试3: API连接测试")
    print("="*60)
    
    from app.core.llm_manager import LLMManager
    
    llm_manager = LLMManager()
    
    print("\n  正在发送测试请求...")
    start_time = time.time()
    
    result = llm_manager.test_connection()
    
    duration = time.time() - start_time
    print(f"  响应时间: {duration:.2f}秒")
    print(f"  连接结果: {result.get('message', '未知')}")
    print(f"  响应内容: {result.get('response', '无响应')[:100] if result.get('response') else '无响应'}")
    print(f"  使用提供商: {result.get('provider', '未知')}")
    
    assert result.get("success"), f"API连接应该成功: {result.get('message', '未知错误')}"
    print("\n  ✅ API连接成功")


def test_rule_matching():
    """测试规则匹配功能"""
    print("\n" + "="*60)
    print("测试4: 规则匹配功能")
    print("="*60)
    
    from app.core.llm_manager import RuleMatchingEngine
    
    engine = RuleMatchingEngine()
    
    test_cases = [
        "电赛国赛一等奖加多少分？",
        "英语六级过了加多少分？",
    ]
    
    for query in test_cases:
        print(f"\n  测试: '{query}'")
        result = engine.match(query)
        print(f"  匹配结果: {result.get('result', '无结果')[:50]}...")
        print(f"  置信度: {result.get('confidence', 0)}")
        assert result is not None, f"规则匹配应该返回结果: {query}"
    
    print("\n  ✅ 规则匹配功能测试完成")


def test_stream_generation():
    """测试流式生成"""
    print("\n" + "="*60)
    print("测试5: 流式生成测试")
    print("="*60)
    
    from app.core.llm_manager import LLMManager
    
    llm_manager = LLMManager()
    
    print("\n  正在测试流式生成...")
    test_prompt = "请用一句话回答：1+1等于几？"
    
    chunks = []
    for chunk in llm_manager.generate_stream(test_prompt):
        chunks.append(chunk)
        print(f"  收到chunk: {chunk[:30]}..." if len(chunk) > 30 else f"  收到chunk: {chunk}")
    
    full_response = "".join(chunks)
    print(f"\n  完整响应: {full_response[:100] if full_response else '无响应'}")
    
    assert len(chunks) > 0, "流式生成应该返回数据"
    print("\n  ✅ 流式生成成功")


def test_xunfei_provider():
    """测试讯飞提供商"""
    print("\n" + "="*60)
    print("测试6: 讯飞星火大模型测试")
    print("="*60)
    
    from app.core.llm_manager import LLMManager
    
    llm_manager = LLMManager()
    
    xunfei_provider = llm_manager.get_provider("xunfei")
    
    assert xunfei_provider is not None, "讯飞星火大模型应该已启用"
    
    print(f"\n  讯飞提供商状态: 已启用")
    assert xunfei_provider.is_available(), "讯飞提供商应该可用"
    print(f"  可用性: 是")
    
    print("\n  正在测试讯飞API连接...")
    start_time = time.time()
    
    test_prompt = "你好，请回复'连接成功'"
    response = xunfei_provider.generate(test_prompt)
    
    duration = time.time() - start_time
    print(f"  响应时间: {duration:.2f}秒")
    print(f"  响应内容: {response}")
    
    assert response, "讯飞星火大模型应该返回响应"
    print("\n  ✅ 讯飞星火大模型连接成功")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# AI连接测试")
    print("#"*60)
    
    results = {}
    
    tests = [
        ("配置加载", test_config_loaded),
        ("LLM管理器", test_llm_manager),
        ("API连接", test_api_connection),
        ("规则匹配", test_rule_matching),
        ("流式生成", test_stream_generation),
        ("讯飞模型", test_xunfei_provider),
    ]
    
    for name, test_func in tests:
        try:
            test_func()
            results[name] = True
        except AssertionError as e:
            print(f"❌ {name} 测试失败: {e}")
            results[name] = False
        except Exception as e:
            print(f"❌ {name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n总计: {passed}/{total} 测试通过")
    
    return passed >= 4


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
