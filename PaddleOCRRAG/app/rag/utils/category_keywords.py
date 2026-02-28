"""
类别关键词库
用于意图识别和类别预测
"""

CATEGORY_KEYWORDS = {
    "C1": {
        "name": "科技类",
        "keywords": [
            "竞赛", "科技", "论文", "专利", "A类", "B类",
            "电子设计", "数学建模", "程序设计", "机器人",
            "创新创业年会", "智能车", "机械创新", "蓝桥杯",
            "互联网+", "挑战杯", "数学竞赛", "物理竞赛",
            "化学竞赛", "生物竞赛", "计算机设计", "软件大赛",
            "嵌入式", "光电设计", "节能减排", "三维设计",
            "工程实践", "材料热处理", "金相技能", "市场调查",
            "电子商务", "成图技术", "数字艺术", "英语演讲",
            "外研社", "正大杯", "西门子", "周培源",
            "力学竞赛", "BIM", "芯片设计", "人工智能大赛"
        ],
        "exclusive_keywords": []
    },
    "C2": {
        "name": "体育类",
        "keywords": [
            "体育", "运动会", "体测", "金牌", "破纪录",
            "田径", "篮球", "足球", "排球", "乒乓球",
            "羽毛球", "网球", "游泳", "健美操", "武术",
            "体育比赛", "运动员", "裁判员", "体育竞赛"
        ],
        "exclusive_keywords": []
    },
    "C3": {
        "name": "文化类",
        "keywords": [
            "英语", "四级", "六级", "CET4", "CET6",
            "证书", "文化", "演讲", "词汇大赛", "亿学杯",
            "计算机二级", "网络工程师", "普通话", "教师资格证",
            "文艺", "朗诵", "辩论", "写作", "征文",
            "摄影", "书法", "绘画", "设计大赛",
            "英语四级", "英语六级", "四六级"
        ],
        "exclusive_keywords": []
    },
    "C4": {
        "name": "创新创业类",
        "keywords": [
            "创业", "互联网+", "挑战杯", "e创", "营业执照",
            "创新创业", "创业大赛", "创业项目", "创业实践",
            "入驻", "孵化", "众创空间", "创业培训",
            "创业年会", "创业计划", "商业模式"
        ],
        "exclusive_keywords": []
    }
}

COMPETITION_TYPE_KEYWORDS = {
    "A": {
        "name": "A类竞赛",
        "keywords": ["A类", "国家级A类", "A类竞赛"],
        "score_map": {
            "国家级一等奖": 30,
            "国家级二等奖": 25,
            "国家级三等奖": 20,
            "省部级一等奖": 20,
            "省部级二等奖": 15,
            "省部级三等奖": 10
        }
    },
    "B": {
        "name": "B类竞赛",
        "keywords": ["B类", "省级B类", "B类竞赛"],
        "score_map": {
            "国家级一等奖": 25,
            "国家级二等奖": 20,
            "国家级三等奖": 15,
            "省部级一等奖": 15,
            "省部级二等奖": 10,
            "省部级三等奖": 8
        }
    },
    "非AB": {
        "name": "非AB类竞赛",
        "keywords": ["非AB", "非A非B", "其他竞赛"],
        "score_map": {},
        "requires_manual_review": True
    }
}

LEVEL_KEYWORDS = {
    "国家级": ["国家级", "国赛", "全国", "国级", "国奖"],
    "省部级": ["省部级", "省赛", "省级", "省奖", "地区级"]
}

AWARD_LEVEL_KEYWORDS = {
    "一等奖": ["一等奖", "金奖", "第一名", "冠军"],
    "二等奖": ["二等奖", "银奖", "第二名", "亚军"],
    "三等奖": ["三等奖", "铜奖", "第三名", "季军"],
    "优秀奖": ["优秀奖", "优胜奖", "参与奖"]
}

SCORE_LIMITS = {
    "C1": {"max": 40, "description": "科技类项目奖励加分上限"},
    "C2": {"max": 20, "description": "体育类项目奖励加分上限"},
    "C3": {"max": 20, "description": "文化类项目奖励加分上限"},
    "C4": {"max": 20, "description": "创新创业类项目奖励加分上限"}
}

CERTIFICATE_SCORES = {
    "CET4": {"name": "英语四级", "score": 10, "category": "C3"},
    "CET6": {"name": "英语六级", "score": 10, "category": "C3"},
    "NCRE2": {"name": "计算机二级", "score": 5, "category": "C3"},
    "NCRE3": {"name": "计算机三级", "score": 5, "category": "C3"},
    "NCRE4": {"name": "计算机四级", "score": 5, "category": "C3"},
    "NETWORK_ENGINEER": {"name": "网络工程师", "score": 5, "category": "C3"}
}

def get_category_by_keyword(keyword: str) -> str:
    """根据关键词获取类别"""
    keyword_lower = keyword.lower()
    for cat, info in CATEGORY_KEYWORDS.items():
        if keyword_lower in [k.lower() for k in info["keywords"]]:
            return cat
    return None

def get_all_keywords() -> list:
    """获取所有关键词"""
    all_kw = []
    for cat, info in CATEGORY_KEYWORDS.items():
        all_kw.extend(info["keywords"])
    return list(set(all_kw))
