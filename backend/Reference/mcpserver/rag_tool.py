#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2025/4/29 (Modified: 2025-04-22)
# @File  : rag_tool.py
# @Author: johnson
# @Contact : github: johnson7788
# @Desc  : eg: MCP RAG检索工具
import os.path
import time
from fastmcp import FastMCP
from datetime import datetime
import random
import re

mcp = FastMCP("RAG检索工具")

@mcp.tool()
def search_labor_law(keyword: str) -> str:
    """
    搜索劳动法
    :param keyword: 关键词, eg:
    :return:
    """
    limit = 5
    data = []

    sample_titles = [
        "劳动合同法实施条例解读",
        "职工加班权益保障条款",
        "关于最低工资标准的规定",
        "劳动争议处理指南",
        "用人单位与员工解除合同的条件"
    ]

    sample_contents = [
        "根据《劳动法》，员工每日工作不得超过八小时。加班需支付加班费。用人单位应合理安排工时。法定节假日加班的，应按三倍工资支付。员工享有休息休假的权利。",
        "用人单位不得随意解除劳动合同。解除合同应提前通知员工或支付赔偿金。员工在试用期内享有基本劳动权利。劳动合同应依法签订并明确岗位职责。若解除劳动合同应告知具体理由。",
        "各地最低工资标准应不低于基本生活保障。工资应以货币形式按月支付给员工。不得无故拖欠工资。特殊行业可制定补充协议，但不得低于标准。员工工资调整需征得员工同意。",
        "劳动争议可通过协商、调解、仲裁及诉讼方式解决。企业应设立内部申诉机制。员工有权提出申诉请求。仲裁是解决争议的前置程序。法院诉讼需在法定期限内提交材料。",
        "员工辞职应提前书面通知单位。单位辞退员工应依法进行。不得因怀孕、工伤等非法辞退员工。经济补偿应按在职年限计算。单位应提供解除合同证明。",
    ]

    for idx in range(limit):
        title = sample_titles[idx]
        plain_content = sample_contents[idx]
        doc_id = f"law_{idx+1:03d}"

        fuzzy_res = fuzzy_search(keyword, plain_content, idprefix="01")

        data.append({
            "title": title,
            "id": doc_id,
            "match_sentence": fuzzy_res["match_sentence"],
            "match_sentences": fuzzy_res["match_sentences"],
            "url": "https://cn.bing.com/search?q=" + title,
        })
    res = {"evidence_db": "劳动法", "data": data}
    return res

@mcp.tool()
def search_social_security_law(keyword: str) -> dict:
    """
    搜索社会保障法
    :param keyword: 关键词, eg:
    :return:
    """
    limit = 5
    data = []

    sample_titles = [
        "社会保险法条文精解",
        "养老保险缴纳与待遇",
        "失业保险领取条件说明",
        "医疗保险参保范围解析",
        "加班工资支付与合法权益保障"
    ]

    sample_contents = [
        "《社会保险法》规定，国家建立基本养老保险制度，保障公民老年基本生活。社会保险基金应专款专用。单位和个人均应依法缴纳社会保险费。参保人员享有查询个人权益记录的权利。政府应加强基金监督管理。",
        "职工养老保险由用人单位和职工共同缴费。缴费年限影响退休待遇水平。参保人员退休后按月领取养老金。转移接续跨省账户应在社保平台办理。延迟退休政策将逐步推进。",
        "失业保险覆盖所有城镇用人单位及其职工。失业人员符合条件的可申请失业金。申请人需进行失业登记和求职登记。参保单位应定期申报缴费基数。领取期间需配合参加职业培训。",
        "医疗保险分为职工医保和居民医保。医保基金主要用于支付门诊和住院费用。参保人需在定点医疗机构就医。个人账户余额可用于支付家庭成员费用。医保支付范围需结合药品目录进行结算。",
        "根据《劳动法》及《工资支付暂行规定》，用人单位安排职工加班的，应依法支付加班工资。工作日加班支付不低于工资的150%，休息日安排工作又未安排补休的支付不低于200%，法定节假日加班支付不低于300%。用人单位不得强迫加班，职工有权拒绝非法加班安排。"  # 新增内容
    ]

    for idx in range(limit):
        title = sample_titles[idx]
        plain_content = sample_contents[idx]
        doc_id = f"sslaw_{idx+1:03d}"

        fuzzy_res = fuzzy_search(keyword, plain_content, idprefix="02")

        data.append({
            "title": title,
            "id": doc_id,
            "match_sentence": fuzzy_res["match_sentence"],
            "match_sentences": fuzzy_res["match_sentences"],
            "url": "https://cn.bing.com/search?q=" + title,
        })
    res = {"evidence_db": "社会保障法", "data": data}
    return res

def fuzzy_search(keyword, content: str, idprefix="01") -> str:

    # 输入段落和关键词

    # 按句子切分（中文用句号、问号、感叹号）
    sentences = re.split(r'[。！？!?]', content)
    sentences = [s.strip() for s in sentences if s.strip()]

    # 输出
    match_sentences = []
    id = idprefix + "-" + datetime.now().strftime('%f')[2:5]
    for idx, one in enumerate(sentences):
        min_idx = max(0, idx-2)
        max_idx = min(len(sentences), idx+3)
        prefix_sentence = "\n".join(sentences[min_idx:idx]) + "\n"
        tail_sentence = "\n".join(sentences[idx+1:max_idx]) + "\n"
        match_sentences.append({"id": f"{id}-{idx}", "sentence": one,  "prefix_sentence": prefix_sentence, "tail_sentence": tail_sentence})
    return {"match_sentence": keyword, "match_content": content, "match_sentences": match_sentences}

if __name__ == '__main__':
    result = search_labor_law(keyword="加班")
    print(result)
    result = search_social_security_law(keyword="加班")
    print(result)