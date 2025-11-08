#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用工具函数模块
"""

import uuid


def generate_task_id() -> str:
    """生成唯一的任务ID"""
    return str(uuid.uuid4())
