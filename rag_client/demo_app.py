"""
PaddleOCRRAG API 示例应用

这个示例展示了如何使用PaddleOCRRAG客户端SDK与API交互。
包括文档上传、证书加分计算、AI对话等功能。
"""

import os
import sys
import time
from pathlib import Path

# 添加当前目录到Python路径，以便导入客户端SDK
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paddle_ocrrag_client import PaddleOCRRAGClient, APIError, generate_cache_key


class PaddleOCRRAGDemo:
    """PaddleOCRRAG演示应用"""
    
    def __init__(self, base_url="http://localhost:8000"):
        """初始化演示应用"""
        self.client = PaddleOCRRAGClient(base_url=base_url)
        self.conversation_history = []
    
    def run(self):
        """运行演示"""
        print("=" * 60)
        print("PaddleOCRRAG API 演示应用")
        print("=" * 60)
        
        try:
            # 1. 健康检查
            self.demo_health_check()
            
            # 2. 文档管理
            self.demo_document_management()
            
            # 3. 证书加分计算
            self.demo_certificate_scoring()
            
            # 4. AI对话
            self.demo_ai_chat()
            
            # 5. 配置管理
            self.demo_config_management()
            
            print("\n演示完成！")
            
        except APIError as e:
            print(f"\nAPI错误: {str(e)}")
        except Exception as e:
            print(f"\n错误: {str(e)}")
    
    def demo_health_check(self):
        """演示健康检查"""
        print("\n1. 健康检查")
        print("-" * 30)
        
        # 系统健康检查
        health = self.client.health.check()
        print(f"系统状态: {health.get('status', '未知')}")
        print(f"服务版本: {health.get('version', '未知')}")
        print(f"运行时间: {health.get('uptime', '未知')}")
        
        # LLM连接测试
        print("\n测试LLM连接...")
        try:
            llm_test = self.client.health.test_llm()
            if llm_test.get("success"):
                print("LLM连接成功")
            else:
                print("LLM连接失败")
        except APIError as e:
            print(f"LLM连接测试失败: {str(e)}")
    
    def demo_document_management(self):
        """演示文档管理"""
        print("\n2. 文档管理")
        print("-" * 30)
        
        # 获取现有文档列表
        print("获取文档列表...")
        docs = self.client.documents.list()
        total_docs = docs.get("total", 0)
        print(f"当前共有 {total_docs} 个文档")
        
        # 显示前几个文档
        items = docs.get("items", [])
        if items:
            print("前5个文档:")
            for i, doc in enumerate(items[:5]):
                print(f"  {i+1}. ID: {doc.get('id', 'N/A')}, 文件名: {doc.get('filename', 'N/A')}, 状态: {doc.get('status', 'N/A')}")
        
        # 上传新文档（如果存在示例文档）
        sample_doc = "data/rules/03、计算机学院综合测评实施细则（2025）.docx"
        if os.path.exists(sample_doc):
            print(f"\n上传文档: {sample_doc}")
            try:
                uploaded_doc = self.client.documents.upload(sample_doc, "综测规则文档")
                print(f"上传成功，文档ID: {uploaded_doc.get('id')}")
                
                # 更新文档状态
                doc_id = uploaded_doc.get('id')
                if doc_id:
                    print(f"启用文档: {doc_id}")
                    self.client.documents.update_status(doc_id, "enabled")
                    print("文档状态已更新")
            except APIError as e:
                print(f"文档上传失败: {str(e)}")
        else:
            print(f"未找到示例文档: {sample_doc}")
    
    def demo_certificate_scoring(self):
        """演示证书加分计算"""
        print("\n3. 证书加分计算")
        print("-" * 30)
        
        # 示例证书列表
        certificates = [
            {
                "text": "张三同学在2023年全国大学生数学建模竞赛中获得一等奖",
                "student_info": {"年级": "大三", "专业": "计算机科学"}
            },
            {
                "text": "李四同学通过大学英语六级考试，分数550分",
                "student_info": {"年级": "大二", "专业": "软件工程"}
            },
            {
                "text": "王五同学发表SCI论文一篇，影响因子3.5",
                "student_info": {"年级": "大四", "专业": "计算机科学"}
            }
        ]
        
        # 单个证书计算
        print("单个证书加分计算:")
        cert = certificates[0]
        score_result = self.client.certificates.calculate_score(
            cert["text"], 
            cert["student_info"]
        )
        
        print(f"证书文本: {cert['text']}")
        print(f"类别: {score_result.get('category', 'N/A')}")
        print(f"加分: {score_result.get('score', 'N/A')}")
        print(f"置信度: {score_result.get('confidence', 'N/A')}")
        
        if "reasoning" in score_result:
            print(f"推理过程: {score_result['reasoning']}")
        
        # 批量证书计算
        print("\n批量证书加分计算:")
        batch_data = [
            {"certificate_text": cert["text"], "student_info": cert["student_info"]}
            for cert in certificates
        ]
        
        batch_results = self.client.certificates.batch_calculate(batch_data)
        
        if "results" in batch_results:
            results = batch_results["results"]
            print(f"批量计算完成，共处理 {len(results)} 个证书")
            
            for i, result in enumerate(results):
                print(f"\n证书 {i+1}:")
                print(f"  类别: {result.get('category', 'N/A')}")
                print(f"  加分: {result.get('score', 'N/A')}")
                print(f"  置信度: {result.get('confidence', 'N/A')}")
    
    def demo_ai_chat(self):
        """演示AI对话"""
        print("\n4. AI对话")
        print("-" * 30)
        
        # 示例问题列表
        questions = [
            "你好，我想了解英语四级证书的加分规则",
            "获得国家级奖学金可以加多少分？",
            "发表SCI论文有什么加分政策？"
        ]
        
        # 逐个问题进行对话
        for question in questions:
            print(f"\n问题: {question}")
            
            # 使用RAG进行对话
            reply = self.client.chat.ask(question, use_rag=True, conversation_history=self.conversation_history)
            
            print(f"回复: {reply.get('reply', 'N/A')}")
            
            # 显示相关文档（如果有）
            if "sources" in reply and reply["sources"]:
                print("\n相关文档:")
                for source in reply["sources"]:
                    print(f"  - {source.get('title', 'N/A')} (相似度: {source.get('similarity', 'N/A')})")
            
            # 更新对话历史
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": reply.get('reply', '')})
            
            # 短暂延迟，避免请求过快
            time.sleep(1)
    
    def demo_config_management(self):
        """演示配置管理"""
        print("\n5. 配置管理")
        print("-" * 30)
        
        # 获取LLM配置
        print("获取LLM配置:")
        llm_config = self.client.llm_config.get()
        print(f"  启用状态: {llm_config.get('enabled', False)}")
        print(f"  API密钥: {'已设置' if llm_config.get('api_key') else '未设置'}")
        print(f"  模型ID: {llm_config.get('model_id', 'N/A')}")
        print(f"  API基础URL: {llm_config.get('api_base_url', 'N/A')}")
        print(f"  温度: {llm_config.get('temperature', 'N/A')}")
        print(f"  最大令牌数: {llm_config.get('max_tokens', 'N/A')}")
        
        # 获取Prompt配置
        print("\n获取Prompt配置:")
        prompts_config = self.client.prompts.get()
        
        if "certificate_analysis" in prompts_config:
            print("  证书分析Prompt已配置")
        
        if "chat" in prompts_config:
            print("  对话Prompt已配置")
        
        # 注意：这里不实际修改配置，仅展示如何操作
        print("\n注意: 演示模式不实际修改配置")
        print("  要修改LLM配置，可以使用: client.llm_config.update(config_data)")
        print("  要修改Prompt配置，可以使用: client.prompts.update(prompts_data)")


def interactive_demo():
    """交互式演示"""
    print("=" * 60)
    print("PaddleOCRRAG API 交互式演示")
    print("=" * 60)
    
    # 创建客户端
    base_url = input("请输入API基础URL (默认: http://localhost:8000): ").strip()
    if not base_url:
        base_url = "http://localhost:8000"
    
    client = PaddleOCRRAGClient(base_url=base_url)
    
    # 交互式菜单
    while True:
        print("\n请选择操作:")
        print("1. 健康检查")
        print("2. 文档管理")
        print("3. 证书加分计算")
        print("4. AI对话")
        print("5. 配置管理")
        print("0. 退出")
        
        choice = input("请输入选项 (0-5): ").strip()
        
        if choice == "0":
            print("再见！")
            break
        elif choice == "1":
            try:
                health = client.health.check()
                print(f"系统状态: {health.get('status', '未知')}")
                print(f"服务版本: {health.get('version', '未知')}")
                
                llm_test = client.health.test_llm()
                print(f"LLM连接: {'成功' if llm_test.get('success') else '失败'}")
            except APIError as e:
                print(f"错误: {str(e)}")
        
        elif choice == "2":
            try:
                docs = client.documents.list()
                total = docs.get("total", 0)
                print(f"当前共有 {total} 个文档")
                
                if total > 0:
                    items = docs.get("items", [])
                    print("前5个文档:")
                    for i, doc in enumerate(items[:5]):
                        print(f"  {i+1}. ID: {doc.get('id', 'N/A')}, 文件名: {doc.get('filename', 'N/A')}, 状态: {doc.get('status', 'N/A')}")
                
                # 上传文档
                file_path = input("请输入要上传的文件路径 (留空跳过): ").strip()
                if file_path and os.path.exists(file_path):
                    description = input("请输入文档描述 (可选): ").strip()
                    uploaded_doc = client.documents.upload(file_path, description)
                    print(f"上传成功，文档ID: {uploaded_doc.get('id')}")
                    
                    # 更新状态
                    doc_id = uploaded_doc.get('id')
                    if doc_id:
                        status = input("请输入文档状态 (enabled/disabled, 默认enabled): ").strip()
                        if not status:
                            status = "enabled"
                        client.documents.update_status(doc_id, status)
                        print("文档状态已更新")
                
            except APIError as e:
                print(f"错误: {str(e)}")
        
        elif choice == "3":
            try:
                cert_text = input("请输入证书文本: ").strip()
                if not cert_text:
                    print("证书文本不能为空")
                    continue
                
                # 学生信息
                print("请输入学生信息 (可选):")
                grade = input("年级 (如 大三): ").strip()
                major = input("专业 (如 计算机科学): ").strip()
                
                student_info = {}
                if grade:
                    student_info["年级"] = grade
                if major:
                    student_info["专业"] = major
                
                # 计算加分
                score_result = client.certificates.calculate_score(cert_text, student_info if student_info else None)
                
                print(f"类别: {score_result.get('category', 'N/A')}")
                print(f"加分: {score_result.get('score', 'N/A')}")
                print(f"置信度: {score_result.get('confidence', 'N/A')}")
                
                if "reasoning" in score_result:
                    print(f"推理过程: {score_result['reasoning']}")
                
            except APIError as e:
                print(f"错误: {str(e)}")
        
        elif choice == "4":
            try:
                question = input("请输入问题: ").strip()
                if not question:
                    print("问题不能为空")
                    continue
                
                use_rag = input("是否使用RAG检索 (y/n, 默认y): ").strip().lower()
                use_rag = use_rag != 'n'
                
                reply = client.chat.ask(question, use_rag=use_rag)
                
                print(f"回复: {reply.get('reply', 'N/A')}")
                
                # 显示相关文档（如果有）
                if "sources" in reply and reply["sources"]:
                    print("\n相关文档:")
                    for source in reply["sources"]:
                        print(f"  - {source.get('title', 'N/A')} (相似度: {source.get('similarity', 'N/A')})")
                
            except APIError as e:
                print(f"错误: {str(e)}")
        
        elif choice == "5":
            try:
                # LLM配置
                print("\nLLM配置:")
                llm_config = client.llm_config.get()
                print(f"  启用状态: {llm_config.get('enabled', False)}")
                print(f"  API密钥: {'已设置' if llm_config.get('api_key') else '未设置'}")
                print(f"  模型ID: {llm_config.get('model_id', 'N/A')}")
                
                # Prompt配置
                print("\nPrompt配置:")
                prompts_config = client.prompts.get()
                
                if "certificate_analysis" in prompts_config:
                    print("  证书分析Prompt已配置")
                
                if "chat" in prompts_config:
                    print("  对话Prompt已配置")
                
                # 测试LLM连接
                test_choice = input("\n是否测试LLM连接 (y/n, 默认n): ").strip().lower()
                if test_choice == 'y':
                    llm_test = client.health.test_llm()
                    if llm_test.get("success"):
                        print("LLM连接成功")
                    else:
                        print("LLM连接失败")
                
            except APIError as e:
                print(f"错误: {str(e)}")
        
        else:
            print("无效选项，请重新输入")


if __name__ == "__main__":
    # 检查是否使用交互式模式
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_demo()
    else:
        # 运行自动演示
        demo = PaddleOCRRAGDemo()
        demo.run()
        
        print("\n要运行交互式演示，请使用: python demo_app.py --interactive")