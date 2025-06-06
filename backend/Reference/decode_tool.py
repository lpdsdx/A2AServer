#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2025/5/13 10:59
# @File  : decode_tool.py
# @Author: johnson
# @Contact : github: johnson7788
# @Desc  :
import os
import logging
import json
import traceback
from typing import List, Dict, Callable, Any

logger = logging.getLogger(__name__)

# 函数名称到
name2human = {
    'SearchTool_search_labor_law': '劳动法',
    'SearchTool_search_social_security_law': '社会保障法',
}

def decode_tool_calls_to_string(raw_str: str) -> str:
    """
    使用预设的工具配置解析工具调用信息。

    Args:
        raw_str: 原始的工具调用字符串。
        tool_config: 一个字典，键是工具名称，值是解析参数的函数。

    Returns:
        人性化的工具调用描述字符串。
    """
    logger.info(f"decode_tool_calls_to_string: raw_str: {raw_str}")
    tool_calls = json.loads(raw_str)
    thoughts = []
    for call in tool_calls:
        function_name = call["function"]["name"]
        arguments = call["function"]["arguments"]
        # 人类能看懂的函数名称
        human_fuction_name = name2human.get(function_name)
        thoughts.append({
            "name": human_fuction_name,
            "arguments": arguments,
            "display": "正在检索" + human_fuction_name + "\n",
            "status": "Working"
        })
    result = {"type": "tool_calls", "data": thoughts}
    return result

def decode_tool_result_to_string(raw_str: str) -> str:
    logger.info(f"decode_tool_result_to_string: raw_str: {raw_str}")
    try:
        raw_dict = json.loads(raw_str)
        function_name = raw_dict["name"]
        human_name = name2human.get(function_name,function_name)
        raw_dict["name"] = human_name
        raw_dict["display"] = "检索" + human_name + "完成\n"
        raw_dict["status"] = "Done"
        result = {"type": "tool_result", "data": [raw_dict]}
        return result
    except Exception  as e:
        logger.error(f"decode_tool_result_to_string: json.loads error: {e}")
        return {"error": f"工具解析json错误: {raw_str}"}
