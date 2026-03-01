"""
日志系统测试脚本
验证日志记录功能是否正常工作
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logger import (
    get_logger, 
    setup_logging, 
    LogContext, 
    rag_logger,
    mask_sensitive_data,
    mask_dict,
    set_request_id,
    set_user_id,
    get_request_id,
    get_user_id,
    RequestContext,
    performance_monitor,
    log_analyzer,
    track_performance,
    clear_context
)


def test_basic_logging():
    """测试基础日志功能"""
    print("\n" + "="*60)
    print("测试1: 基础日志功能")
    print("="*60)
    
    logger = get_logger("test_module")
    
    logger.debug("这是一条DEBUG日志")
    logger.info("这是一条INFO日志")
    logger.warning("这是一条WARNING日志")
    logger.error("这是一条ERROR日志")
    logger.critical("这是一条CRITICAL日志")
    
    logger.info("带参数的日志", extra={'params': {'key': 'value', 'count': 123}})
    
    assert logger is not None, "日志器应该成功创建"
    print("✅ 基础日志测试完成")


def test_request_context():
    """测试请求上下文"""
    print("\n" + "="*60)
    print("测试2: 请求上下文追踪")
    print("="*60)
    
    logger = get_logger("test_context")
    
    request_id = set_request_id()
    print(f"  设置请求ID: {request_id}")
    assert request_id is not None, "请求ID应该被设置"
    
    set_user_id("user_12345")
    print(f"  设置用户ID: user_12345")
    
    logger.info("带请求上下文的日志")
    
    current_rid = get_request_id()
    current_uid = get_user_id()
    print(f"  获取请求ID: {current_rid}")
    print(f"  获取用户ID: {current_uid}")
    assert current_rid == request_id, "请求ID应该匹配"
    assert current_uid == "user_12345", "用户ID应该匹配"
    
    clear_context()
    logger.info("清除上下文后的日志")
    
    print("✅ 请求上下文测试完成")


def test_request_context_manager():
    """测试请求上下文管理器"""
    print("\n" + "="*60)
    print("测试3: 请求上下文管理器")
    print("="*60)
    
    logger = get_logger("test_context_mgr")
    
    with RequestContext(request_id="test_req_001", user_id="test_user"):
        logger.info("在上下文管理器内的日志")
        rid = get_request_id()
        uid = get_user_id()
        print(f"  请求ID: {rid}")
        print(f"  用户ID: {uid}")
        assert rid == "test_req_001", "请求ID应该匹配"
        assert uid == "test_user", "用户ID应该匹配"
    
    logger.info("退出上下文管理器后的日志")
    print(f"  请求ID: {get_request_id() or '(空)'}")
    
    print("✅ 请求上下文管理器测试完成")


def test_sensitive_data_masking():
    """测试敏感数据过滤"""
    print("\n" + "="*60)
    print("测试4: 敏感数据过滤")
    print("="*60)
    
    test_cases = [
        ("api_key=abc123", "api_key应被过滤"),
        ("password=secret123", "password应被过滤"),
        ("token=xyz789", "token应被过滤"),
        ("normal_data=value", "普通数据应保留"),
    ]
    
    for data, desc in test_cases:
        masked = mask_sensitive_data(data)
        print(f"  {desc}: '{data}' -> '{masked}'")
        if "api_key" in data or "password" in data or "token" in data:
            assert "***" in masked, f"敏感数据应该被过滤: {data}"
    
    test_dict = {
        "api_key": "secret_key_123",
        "password": "my_password",
        "normal_field": "normal_value",
        "nested": {
            "token": "nested_token"
        }
    }
    
    masked_dict = mask_dict(test_dict)
    print(f"\n  字典过滤结果: {masked_dict}")
    assert masked_dict["api_key"] != "secret_key_123", "api_key应该被过滤"
    assert masked_dict["password"] != "my_password", "password应该被过滤"
    assert masked_dict["normal_field"] == "normal_value", "普通字段应该保留"
    
    print("✅ 敏感数据过滤测试完成")


def test_log_context():
    """测试日志上下文管理器"""
    print("\n" + "="*60)
    print("测试5: 日志上下文管理器")
    print("="*60)
    
    logger = get_logger("test_log_context")
    
    with LogContext(logger, "测试操作", {"param1": "value1"}):
        logger.info("执行中...")
        time.sleep(0.1)
    
    print("✅ 日志上下文测试完成")


def test_performance_tracking():
    """测试性能追踪"""
    print("\n" + "="*60)
    print("测试6: 性能追踪")
    print("="*60)
    
    @track_performance("test_operation")
    def slow_function():
        time.sleep(0.1)
        return "done"
    
    result = slow_function()
    print(f"  函数执行结果: {result}")
    assert result == "done", "函数应该返回 'done'"
    
    stats = performance_monitor.get_stats("test_operation")
    print(f"  性能统计: {stats}")
    assert stats is not None, "应该有性能统计"
    
    print("✅ 性能追踪测试完成")


def test_rag_logger():
    """测试RAG专用日志器"""
    print("\n" + "="*60)
    print("测试7: RAG专用日志器")
    print("="*60)
    
    rag_logger.log_query("电赛国赛一等奖加多少分？", {"sub_category": "C1"})
    
    rag_logger.log_retrieval(
        query="电赛国赛一等奖",
        filter_conditions={"sub_category": "C1"},
        result_count=5,
        duration_ms=150
    )
    
    rag_logger.log_rerank(
        input_count=10,
        output_count=5,
        top_score=0.85,
        duration_ms=20
    )
    
    rag_logger.log_competition_match(
        input_name="电赛",
        matched_name="全国大学生电子设计竞赛（国赛）",
        match_score=95.0,
        competition_type="A"
    )
    
    rag_logger.log_document_load(
        source="test.xlsx",
        doc_count=1,
        chunk_count=171,
        duration_ms=500
    )
    
    rag_logger.log_performance("test_operation", 100, {"detail": "test"})
    
    assert rag_logger is not None, "RAG日志器应该存在"
    print("✅ RAG专用日志器测试完成")


def test_error_logging():
    """测试错误日志"""
    print("\n" + "="*60)
    print("测试8: 错误日志")
    print("="*60)
    
    logger = get_logger("test_error")
    
    try:
        raise ValueError("这是一个测试错误")
    except Exception as e:
        logger.error(f"捕获到异常: {e}", exc_info=True)
    
    rag_logger.log_error("test_operation", Exception("测试错误"), {"context": "test"})
    
    print("✅ 错误日志测试完成")


def test_performance_monitor():
    """测试性能监控器"""
    print("\n" + "="*60)
    print("测试9: 性能监控器")
    print("="*60)
    
    performance_monitor.record("operation_a", 100, True, {"detail": "fast"})
    performance_monitor.record("operation_a", 200, True, {"detail": "medium"})
    performance_monitor.record("operation_a", 1500, True, {"detail": "slow"})
    performance_monitor.record("operation_b", 50, True)
    
    stats_a = performance_monitor.get_stats("operation_a")
    print(f"  operation_a 统计: {stats_a}")
    assert stats_a is not None, "应该有统计数据"
    assert stats_a.get("count", 0) >= 3, "应该有至少3条记录"
    
    slow_ops = performance_monitor.get_slow_operations(threshold_ms=1000)
    print(f"  慢操作: {slow_ops}")
    
    summary = performance_monitor.get_operations_summary()
    print(f"  操作摘要: {summary}")
    assert len(summary) >= 2, "应该有至少2个操作的摘要"
    
    print("✅ 性能监控器测试完成")


def test_log_analyzer():
    """测试日志分析器"""
    print("\n" + "="*60)
    print("测试10: 日志分析器")
    print("="*60)
    
    logger = get_logger("test_analyzer")
    
    for i in range(3):
        logger.info(f"测试日志消息 {i+1}")
    
    logger.error("测试错误消息")
    
    results = log_analyzer.search_logs(keyword="测试", limit=10)
    print(f"  搜索结果数量: {len(results)}")
    
    error_summary = log_analyzer.get_error_summary(hours=1)
    print(f"  错误摘要: {error_summary}")
    
    print("✅ 日志分析器测试完成")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# 日志系统测试")
    print("#"*60)
    
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    
    setup_logging(
        log_level="DEBUG",
        log_dir=log_dir,
        log_format="console",
        enable_file=True
    )
    
    print(f"\n日志目录: {log_dir}")
    
    results = {}
    
    tests = [
        ("基础日志功能", test_basic_logging),
        ("请求上下文追踪", test_request_context),
        ("请求上下文管理器", test_request_context_manager),
        ("敏感数据过滤", test_sensitive_data_masking),
        ("日志上下文管理器", test_log_context),
        ("性能追踪", test_performance_tracking),
        ("RAG专用日志器", test_rag_logger),
        ("错误日志", test_error_logging),
        ("性能监控器", test_performance_monitor),
        ("日志分析器", test_log_analyzer),
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
    print(f"\n日志文件已保存到: {log_dir}")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
