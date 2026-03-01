"""
RAG类别感知检索测试脚本
测试各模块功能是否正常工作

注意: 部分 test 需要 langchain，在 Windows 环境下可能因 numpy/transformers 
兼容性问题而崩溃。设置环境变量 SKIP_LANGCHAIN_TESTS=1 可跳过这些测试。
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_category_keywords():
    """测试类别关键词库"""
    print("\n" + "="*60)
    print("测试1: 类别关键词库")
    print("="*60)
    
    from app.rag.utils.category_keywords import (
        CATEGORY_KEYWORDS,
        COMPETITION_TYPE_KEYWORDS,
        SCORE_LIMITS,
        CERTIFICATE_SCORES
    )
    
    print("\n类别关键词:")
    for cat, info in CATEGORY_KEYWORDS.items():
        print(f"  {cat} ({info['name']}): {len(info['keywords'])} 个关键词")
    
    print("\n竞赛类型加分规则:")
    for comp_type, info in COMPETITION_TYPE_KEYWORDS.items():
        print(f"  {comp_type} ({info['name']}):")
        if info.get('score_map'):
            for key, score in info['score_map'].items():
                print(f"    {key}: {score}分")
    
    print("\n分数上限:")
    for cat, info in SCORE_LIMITS.items():
        print(f"  {cat}: 最高{info['max']}分 ({info['description']})")
    
    print("\n证书加分:")
    for cert_type, info in CERTIFICATE_SCORES.items():
        print(f"  {info['name']}: {info['score']}分 (类别: {info['category']})")
    
    return True


def test_competition_mapper():
    """测试竞赛名称映射器"""
    print("\n" + "="*60)
    print("测试2: 竞赛名称映射器")
    print("="*60)
    
    from app.rag.preprocessors.competition_mapper import CompetitionMapper
    
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "rules", "05、学科竞赛名称列表.xlsx"
    )
    
    mapper = CompetitionMapper(excel_path)
    
    test_cases = [
        "电赛",
        "数学建模",
        "蓝桥杯",
        "互联网+",
        "英语四级",
        "全国大学生电子设计竞赛（国赛）",
        "亿学杯英语词汇大赛"
    ]
    
    for name in test_cases:
        std_name, info, score = mapper.normalize_name(name)
        print(f"\n输入: {name}")
        print(f"  标准名称: {std_name}")
        print(f"  匹配分数: {score}")
        if info:
            print(f"  竞赛类型: {info.competition_type}")
            print(f"  级别: {info.level}")
            print(f"  需人工审核: {info.requires_manual_review}")
    
    print(f"\n总共加载 {len(mapper.get_all_competitions())} 条竞赛记录")
    return True


def test_intent_recognizer():
    """测试意图识别器"""
    print("\n" + "="*60)
    print("测试3: 意图识别器")
    print("="*60)
    
    from app.rag.preprocessors.intent_recognizer import IntentRecognizer
    from app.rag.preprocessors.competition_mapper import CompetitionMapper
    
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "rules", "05、学科竞赛名称列表.xlsx"
    )
    
    recognizer = IntentRecognizer()
    recognizer.competition_mapper = CompetitionMapper(excel_path)
    
    test_queries = [
        "电赛国赛一等奖加多少分？",
        "英语六级过了加多少分？",
        "体育运动会获奖怎么算？",
        "互联网+创业比赛加分吗？",
        "计算机二级证书加分吗？",
        "A类竞赛国家级一等奖加多少分？",
        "亿学杯英语竞赛能加分吗？"
    ]
    
    for query in test_queries:
        intent = recognizer.recognize(query)
        print(f"\n查询: {query}")
        print(f"  主类别: {intent.main_category}")
        print(f"  子类别: {intent.sub_category}")
        print(f"  竞赛类型: {intent.competition_type}")
        print(f"  级别: {intent.level}")
        print(f"  获奖等级: {intent.award_level}")
        print(f"  证书类型: {intent.certificate_type}")
        print(f"  置信度: {intent.confidence:.2f}")
        print(f"  需人工审核: {intent.requires_manual_review}")
        print(f"  匹配关键词: {intent.matched_keywords}")
    
    return True


def test_query_enhancer():
    """测试查询增强器"""
    print("\n" + "="*60)
    print("测试4: 查询增强器")
    print("="*60)
    
    from app.rag.preprocessors.query_enhancer import QueryEnhancer
    from app.rag.preprocessors.intent_recognizer import IntentRecognizer
    from app.rag.preprocessors.competition_mapper import CompetitionMapper
    
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "rules", "05、学科竞赛名称列表.xlsx"
    )
    
    enhancer = QueryEnhancer()
    enhancer.intent_recognizer = IntentRecognizer()
    enhancer.intent_recognizer.competition_mapper = CompetitionMapper(excel_path)
    
    test_queries = [
        "电赛国赛一等奖加多少分？",
        "英语六级过了加多少分？",
        "体育运动会获奖怎么算？",
        "亿学杯英语竞赛能加分吗？"
    ]
    
    for query in test_queries:
        context = enhancer.get_search_context(query)
        print(f"\n原始查询: {query}")
        print(f"  增强查询: {context['enhanced_query']}")
        print(f"  元数据过滤器: {context['metadata_filter']}")
        print(f"  需人工审核: {context['requires_manual_review']}")
    
    return True


@pytest.mark.skip_if_no_langchain
def test_enhanced_loader():
    """测试增强文档加载器"""
    print("\n" + "="*60)
    print("测试5: 增强文档加载器")
    print("="*60)
    
    from app.rag.loaders.enhanced_loader import EnhancedRuleLoader
    from app.rag.preprocessors.competition_mapper import CompetitionMapper
    
    rules_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "rules"
    )
    
    loader = EnhancedRuleLoader()
    loader.competition_mapper = CompetitionMapper(os.path.join(rules_path, "05、学科竞赛名称列表.xlsx"))
    loader.load_all_documents(rules_path)
    
    stats = loader.get_stats()
    print(f"\n统计信息:")
    print(f"  总chunk数: {stats['total_chunks']}")
    print(f"  按类型: {stats['by_type']}")
    print(f"  按子类别: {stats['by_sub_category']}")
    print(f"  按竞赛类型: {stats['by_competition_type']}")
    
    print(f"\n前3个chunk示例:")
    for i, chunk in enumerate(loader.get_chunks()[:3]):
        print(f"\n  Chunk {i+1}:")
        print(f"    文本: {chunk.text[:100]}...")
        print(f"    元数据: {chunk.metadata}")
    
    return True


def test_reranker():
    """测试重排器"""
    print("\n" + "="*60)
    print("测试6: 类别感知重排器")
    print("="*60)
    
    import sys
    import importlib.util
    
    spec = importlib.util.spec_from_file_location(
        "reranker",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "app", "rag", "vector_db", "reranker.py")
    )
    reranker_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reranker_module)
    
    CategoryReranker = reranker_module.CategoryReranker
    
    spec2 = importlib.util.spec_from_file_location(
        "intent_recognizer",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "app", "rag", "preprocessors", "intent_recognizer.py")
    )
    intent_module = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(intent_module)
    
    IntentResult = intent_module.IntentResult
    
    reranker = CategoryReranker()
    
    mock_results = {
        "documents": [
            "【主类:C｜子类:C1｜竞赛类型:A｜级别:国家级】A类国家级一等奖加30分",
            "【主类:C｜子类:C1｜竞赛类型:B｜级别:国家级】B类国家级一等奖加25分",
            "【主类:C｜子类:C3】英语六级通过加10分"
        ],
        "metadatas": [
            {"type": "rule", "main_category": "C", "sub_category": "C1", "competition_type": "A", "level": "国家级", "score": 30},
            {"type": "rule", "main_category": "C", "sub_category": "C1", "competition_type": "B", "level": "国家级", "score": 25},
            {"type": "rule", "main_category": "C", "sub_category": "C3", "certificate_type": "CET6", "score": 10}
        ],
        "distances": [0.2, 0.25, 0.3]
    }
    
    query = "电赛国赛一等奖加多少分？"
    intent = IntentResult(
        main_category="C",
        sub_category="C1",
        competition_type="A",
        level="国家级",
        award_level="一等奖",
        confidence=0.9
    )
    
    reranked = reranker.rerank(mock_results, query, intent, top_k=3)
    
    print(f"\n查询: {query}")
    print(f"意图: 子类={intent.sub_category}, 类型={intent.competition_type}, 级别={intent.level}")
    print(f"\n重排结果:")
    for i, result in enumerate(reranked):
        print(f"\n  结果 {i+1}:")
        print(f"    文本: {result.document[:60]}...")
        print(f"    重排分数: {result.reranked_score:.3f}")
        print(f"    分数明细: {result.score_breakdown}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# RAG类别感知检索系统测试")
    print("#"*60)
    
    results = {}
    
    try:
        results["类别关键词库"] = test_category_keywords()
    except Exception as e:
        print(f"类别关键词库测试失败: {e}")
        import traceback
        traceback.print_exc()
        results["类别关键词库"] = False
    
    try:
        results["竞赛名称映射器"] = test_competition_mapper()
    except Exception as e:
        print(f"竞赛名称映射器测试失败: {e}")
        import traceback
        traceback.print_exc()
        results["竞赛名称映射器"] = False
    
    try:
        results["意图识别器"] = test_intent_recognizer()
    except Exception as e:
        print(f"意图识别器测试失败: {e}")
        import traceback
        traceback.print_exc()
        results["意图识别器"] = False
    
    try:
        results["查询增强器"] = test_query_enhancer()
    except Exception as e:
        print(f"查询增强器测试失败: {e}")
        import traceback
        traceback.print_exc()
        results["查询增强器"] = False
    
    try:
        results["增强文档加载器"] = test_enhanced_loader()
    except Exception as e:
        print(f"增强文档加载器测试失败: {e}")
        import traceback
        traceback.print_exc()
        results["增强文档加载器"] = False
    
    try:
        results["类别感知重排器"] = test_reranker()
    except Exception as e:
        print(f"类别感知重排器测试失败: {e}")
        import traceback
        traceback.print_exc()
        results["类别感知重排器"] = False
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n总计: {passed}/{total} 测试通过")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
