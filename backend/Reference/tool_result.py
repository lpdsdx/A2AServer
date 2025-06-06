#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2025/6/3 10:24
# @File  : tool_result.py.py
# @Author: johnson
# @Contact : github: johnson7788
# @Desc  :

import json
import logging

logger = logging.getLogger(__name__)


def tool_process_result(tool_name, result_content):
    """
    处理工具的结果
    """
    print(f"工具结果处理中...，为了给LLM模型使用,{tool_name}")
    # 尝试加载成dict
    try:
        result_dict = json.loads(result_content)
        contents = ""
        data = result_dict.get("data", [])
        for item in data:
            match_sentences = item.get("match_sentences")
            for one_sentence in match_sentences:
                sentence_id = one_sentence.get("id")
                sentence = one_sentence.get("sentence")
                contents += f"{sentence_id} -- {sentence}\n"
            contents += "\n"
        return {"data": result_dict, "contents": contents}
    except Exception as e:
        logger.error(f"工具{tool_name}运行结果解析失败: {e}")
        return result_content
    return result_content


if __name__ == '__main__':
    tool_name = "SearchEvidence"
    result_content = """{
  "evidence_db": "循证库",
  "data": [
    {
      "title": "atypia and lobular carcinoma in situ high risk lesions of the breast",
      "match_sentence": "治疗方案包括选择性雌激素受体调节剂和芳香酶抑制剂",
      "match_content": "因此，美国癌症协会(American Cancer Society, ACS)、NCCN等重要机构指南推荐，乳腺MRI仅用于监测乳腺癌高危女性；即估计乳腺癌的终生发病风险＞20%-25%的女性，该风险通过BRCAPRO模型或基于家族史的相似模型得出，而不是使用Gail模型得出[53,113]。(参见“乳腺癌筛查：效果和危害的证据”，关于‘MRI’一节)化学预防—建议对AH或LCIS患者给予内分泌治疗作为化学预防，而不是仅观察[114]。其目的是预防浸润性乳腺癌；尚无证据显示化学预防可增加高危病变患者的生存率。治疗方案包括选择性雌激素受体调节剂和芳香酶抑制剂。药物选择和疗程详见其他专题。(参见“选择性雌激素受体调节剂和芳香酶抑制剂的乳腺癌预防作用”)学会指南链接—部分国家及地区的学会指南和政府指南的链接参见其他专题。(参见“Society guideline links: Evaluation of breast problems”)总结与推荐●乳腺高危病变–乳腺良性病变一般分为3类：非增生性病变、良性增生和不典型增生(atypical hyperplasia, AH)",
      "id": "01-676534"
    },
    {
      "title": "breast ductal carcinoma in situ epidemiology clinical manifestations and diagnosis",
      "match_sentence": "治疗旨在预防浸润性乳腺癌",
      "match_content": "Authors:Laura C Collins, MDChristine Laronga, MD, FACSJulia S Wong, MDSection Editors:Lori J Pierce, MDDaniel F Hayes, MDAnees B Chagpar, MD, MSc, MA, MPH, MBA, FACS, FRCS(C)Gary J Whitman, MDDeputy Editor:Wenliang Chen, MD, PhD翻译:李孝远, 主治医师Contributor Disclosures所有专题都会依据新发表的证据和同行评议过程而更新。文献评审有效期至：2025-04.专题最后更新日期：2024-02-08.引言—乳腺导管原位癌(ductal carcinoma in situ, DCIS)包括一系列局限于乳腺导管和乳腺小叶的肿瘤，组织学和生物潜能各不相同。引入乳腺X线钼靶摄影筛查后，该病诊断显著增加[1]。治疗旨在预防浸润性乳腺癌。本专题将讨论DCIS的诊断、评估和鉴别诊断，治疗参见其他专题。(参见“导管原位癌的治疗和预后”)DCIS的病理标准详见其他专题。(参见“乳腺癌的病理学”，关于‘导管原位癌’一节)流行病学和危险因素发病率—DCIS的发病率从20世纪70年代的5.8例/100,000名女性显著增加至2004年的32.5例/100,000名女性，随后进入了平台期[1-3]",
      "id": "01-676982"
    },
    {
      "title": "breast biopsy",
      "match_sentence": "这些影像学检查用于确定哪些病变应切除或接受恶性肿瘤新辅助治疗，并指导制定合适的治疗方案",
      "match_content": ")●基础篇(参见“患者教育：乳房活检(基础篇)”)总结与推荐●乳腺影像学检查发现可疑异常或乳房触及可疑肿块时，应先行经皮穿刺活检诊断，而非手术活检。一般仅在经皮穿刺活检不可行或结果不确定时，才考虑手术活检。(参见上文‘引言’)●乳腺活检之前应行影像学评估，通常采用乳腺钼靶和/或超声 (流程图 1)。这些影像学检查用于确定哪些病变应切除或接受恶性肿瘤新辅助治疗，并指导制定合适的治疗方案。可根据乳腺影像报告和数据系统(BI-RADS)对影像学上的异常进行癌症风险分类 (表 1)。临床实践指南推荐活检所有BI-RADS 4类和5类病变。(参见上文‘活检前影像学评估’)●大多数患者的乳腺活检方法首选空芯针穿刺活检(CNB)",
      "id": "01-678174"
    },
    {
      "title": "cancer risks in brca1 2 carriers",
      "match_sentence": "●(参见“遗传性乳腺癌和卵巢癌综合征高危人群的基因检测和管理”，关于‘遗传风险评估的标准’一节)●(参见“遗传性乳腺癌和卵巢癌综合征概述”)具有BRCA1/2种系突变患者的处理及癌症诊断详见下列专题：●乳腺癌•(参见“对侧预防性乳房切除术”，关于‘BRCA突变携带者’一节)•(参见“男性乳腺癌”)•(参见“ER/PR阴性、HER2阴性(三阴)乳腺癌”，关于‘BRCA种系突变’一节)•(参见“转移性乳腺癌的治疗概述”，关于‘特殊注意事项’一节)●卵巢癌•(参见“上皮性卵巢癌、输卵管癌或腹膜癌生存者的处理方法”，关于‘携带BRCA突变的EOC患者的乳腺癌风险管理’一节)•(参见“复发性上皮性卵巢癌、输卵管癌或腹膜癌的药物治疗：铂类敏感型疾病”，关于‘BRCA携带者中PARP抑制’一节)•(参见“复发性上皮性卵巢癌、输卵管癌或腹膜癌的药物治疗：铂类耐药型疾病”，关于‘BRCA突变携带者’一节)BRCA1/2致病变异的临床特征—遗传性乳腺癌和卵巢癌大多是由高外显率的BRCA1/2致病种系变异导致，呈常染色体显性遗传",
      "match_content": "本专题将讨论BRCA1/2致病变异携带者的处理。遗传学风险评估的指征见其他专题。非BRCA1/2突变所致的明确高危综合征患者的处理也参见其他专题，如Li-Fraumeni综合征及磷酸酶和张力蛋白同源物(phosphatase and tensin homolog, PTEN)错构瘤综合征。●(参见“遗传性乳腺癌和卵巢癌综合征高危人群的基因检测和管理”，关于‘遗传风险评估的标准’一节)●(参见“遗传性乳腺癌和卵巢癌综合征概述”)具有BRCA1/2种系突变患者的处理及癌症诊断详见下列专题：●乳腺癌•(参见“对侧预防性乳房切除术”，关于‘BRCA突变携带者’一节)•(参见“男性乳腺癌”)•(参见“ER/PR阴性、HER2阴性(三阴)乳腺癌”，关于‘BRCA种系突变’一节)•(参见“转移性乳腺癌的治疗概述”，关于‘特殊注意事项’一节)●卵巢癌•(参见“上皮性卵巢癌、输卵管癌或腹膜癌生存者的处理方法”，关于‘携带BRCA突变的EOC患者的乳腺癌风险管理’一节)•(参见“复发性上皮性卵巢癌、输卵管癌或腹膜癌的药物治疗：铂类敏感型疾病”，关于‘BRCA携带者中PARP抑制’一节)•(参见“复发性上皮性卵巢癌、输卵管癌或腹膜癌的药物治疗：铂类耐药型疾病”，关于‘BRCA突变携带者’一节)BRCA1/2致病变异的临床特征—遗传性乳腺癌和卵巢癌大多是由高外显率的BRCA1/2致病种系变异导致，呈常染色体显性遗传。在某些族群或种族中，BRCA1/2致病种系变异更普遍，例如，德系犹太裔女性。(参见下文‘BRCA1/2致病变异的阳性率’)在BRCA1/2致病变异携带者中，常见几代女性都罹患乳腺癌(多在绝经前发生)。BRCA1/2也可引起其他恶性肿瘤，如卵巢癌、前列腺癌、男性乳腺癌、胰腺癌",
      "id": "01-679923"
    },
    {
      "title": "clinical features diagnosis and staging of newly diagnosed breast cancer",
      "match_sentence": "乳腺癌尽早治疗可以挽救生命",
      "match_content": "也有人大肆鼓吹停止激素替代治疗是导致前述发病率下降的主要原因[7-12]。(参见“绝经期激素治疗的利弊”，关于‘乳腺癌’一节)自20世纪70年代开始，乳腺癌死亡率就一直在下降[13]。原因是乳腺癌筛查提高和辅助治疗的进步[14,15]。乳腺癌尽早治疗可以挽救生命。例如，一篇重要文献显示，40-69岁女性若能有组织地加入乳腺X线钼靶摄影筛查，则诊断后10年和20年内死于乳腺癌的风险分别比未加入筛查者降低60%和47%[16]。乳腺癌的其他危险因素和风险预测模型见其他专题。(参见“改变女性乳腺癌风险的因素”和“乳腺癌筛查的策略和推荐”，关于‘确定乳腺癌风险’一节)临床特征—乳腺癌的诊断需要组织学评估",
      "id": "01-680738"
    }
  ]
}"""
    print(tool_process_result(tool_name, result_content))