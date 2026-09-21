#!/usr/bin/env python3
"""婚姻家庭与继承文书 Word 生成器 —— 符合 NDR §3 规范

用法：
    python generate_family_doc.py --subtype will --title "遗嘱" --output /path/to/output.docx
    python generate_family_doc.py --subtype divorce --title "离婚协议" --output /path/to/output.docx
    python generate_family_doc.py --subtype marital --title "夫妻财产协议" --output /path/to/output.docx

子类型：will | divorce | marital | support-gift | guardianship
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '非争议解决公共标准', 'references'))
from format_docx import create_document
from format_base import *
import argparse
import json


def will_sop(data):
    """遗嘱起草 → content_blocks"""
    blocks = []
    testator = data.get('testator', {})
    blocks.append({'type': 'body',
        'text': f'立遗嘱人：{testator.get("name", "________")}，'
                f'{testator.get("gender", "男")}，'
                f'{testator.get("birth", "____年____月____日")}出生，'
                f'公民身份号码：{testator.get("id", "________________")}，'
                f'住址：{testator.get("address", "________________________________")}。'
    })
    blocks.append({'type': 'body',
        'text': '本人目前身体和精神状态良好，思维清晰，'
                '具备完全民事行为能力。根据《中华人民共和国民法典》'
                '第一千一百三十四条之规定，自愿订立本遗嘱。'
    })

    blocks.append({'type': 'section', 'text': '一、财产状况'})
    estates = data.get('estates', [])
    if estates:
        for i, e in enumerate(estates):
            blocks.append({'type': 'body',
                'text': f'{i+1}. {e.get("description", "________________________________")}'})
    else:
        blocks.append({'type': 'body', 'text': '________________________________'})

    blocks.append({'type': 'section', 'text': '二、财产处分安排'})
    heirs = data.get('heirs', [])
    if heirs:
        for h in heirs:
            blocks.append({'type': 'body',
                'text': f'{h.get("name", "________")}（公民身份号码：'
                        f'{h.get("id", "________________")}，与本人关系：'
                        f'{h.get("relation", "________")}）'
                        f'继承{h.get("asset", "________")}。'
            })
    else:
        blocks.append({'type': 'body', 'text': '________________________________'})

    blocks.append({'type': 'section', 'text': '三、遗产管理人'})
    executor = data.get('executor', '____________')
    blocks.append({'type': 'body',
        'text': f'本人指定{executor}为遗产管理人，负责清理遗产、'
                '处理债权债务、分割遗产并办理过户手续。'
    })

    blocks.append({'type': 'section', 'text': '四、有关说明'})
    blocks.append({'type': 'body',
        'text': '本遗嘱由本人亲笔全文书写，未受任何胁迫、欺诈，系本人真实意思表示。'
    })
    blocks.append({'type': 'body',
        'text': f'本遗嘱一式{data.get("copies", "____")}份，具有同等效力。'
    })

    # 落款
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'body', 'text': '立遗嘱人（亲笔签名）：______________'})
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'body', 'text': '____年____月____日'})
    blocks.append({'type': 'body', 'text': '代书人：无（本遗嘱由立遗嘱人亲笔全文书写）'})
    return blocks


def divorce_sop(data):
    """离婚协议起草 → content_blocks"""
    blocks = []
    parties = data.get('parties', {})
    blocks.append({'type': 'body',
        'text': f'甲方：{parties.get("party_a", {}).get("name", "________")}，'
                f'公民身份号码：{parties.get("party_a", {}).get("id", "________________")}'
    })
    blocks.append({'type': 'body',
        'text': f'乙方：{parties.get("party_b", {}).get("name", "________")}，'
                f'公民身份号码：{parties.get("party_b", {}).get("id", "________________")}'
    })

    blocks.append({'type': 'section', 'text': '一、自愿离婚'})
    blocks.append({'type': 'body', 'text': '甲、乙双方均确认夫妻感情已破裂，自愿解除婚姻关系。'})

    blocks.append({'type': 'section', 'text': '二、子女抚养'})
    children = data.get('children', [])
    if children:
        for c in children:
            blocks.append({'type': 'body',
                'text': f'子女{c.get("name", "____")}（{c.get("birth", "____年____月")}生）由{c.get("custodian", "____")}直接抚养。'
            })
            blocks.append({'type': 'body',
                'text': f'抚养费每月{c.get("support_amount", "________")}元，于每月{c.get("pay_day", "__")}日前支付。'
            })
            blocks.append({'type': 'body',
                'text': f'探望权：{c.get("visitation", "________________________________")}'
            })
    else:
        blocks.append({'type': 'body', 'text': '________________________________'})

    blocks.append({'type': 'section', 'text': '三、财产分割'})
    blocks.append({'type': 'body', 'text': '________________________________'})

    blocks.append({'type': 'section', 'text': '四、债务处理'})
    blocks.append({'type': 'body', 'text': '________________________________'})

    blocks.append({'type': 'section', 'text': '五、附则'})
    blocks.append({'type': 'body',
        'text': '本协议一式三份，甲乙双方各执一份，婚姻登记机关存档一份，自双方签字并领取离婚证之日起生效。'
    })

    # 落款
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'body', 'text': '甲方（亲笔签名）：______________'})
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'body', 'text': '____年____月____日'})
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'body', 'text': '乙方（亲笔签名）：______________'})
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'body', 'text': '____年____月____日'})
    return blocks


def marital_sop(data):
    """夫妻财产协议 → content_blocks"""
    blocks = []
    parties = data.get('parties', {})
    blocks.append({'type': 'body',
        'text': f'甲方：{parties.get("party_a", {}).get("name", "________")}，'
                f'公民身份号码：{parties.get("party_a", {}).get("id", "________________")}'
    })
    blocks.append({'type': 'body',
        'text': f'乙方：{parties.get("party_b", {}).get("name", "________")}，'
                f'公民身份号码：{parties.get("party_b", {}).get("id", "________________")}'
    })

    blocks.append({'type': 'section', 'text': '一、财产归属约定'})
    blocks.append({'type': 'body', 'text': '________________________________'})

    blocks.append({'type': 'section', 'text': '二、债务承担'})
    blocks.append({'type': 'body', 'text': '________________________________'})

    blocks.append({'type': 'section', 'text': '三、生活费用'})
    blocks.append({'type': 'body', 'text': '________________________________'})

    blocks.append({'type': 'section', 'text': '四、附则'})
    blocks.append({'type': 'body',
        'text': '本协议一式两份，甲乙双方各执一份，自双方签字之日起生效。'
    })

    # 落款
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'body', 'text': '甲方（亲笔签名）：______________'})
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'body', 'text': '____年____月____日'})
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'body', 'text': '乙方（亲笔签名）：______________'})
    blocks.append({'type': 'blank'})
    blocks.append({'type': 'body', 'text': '____年____月____日'})
    return blocks


SOP_MAP = {
    'will': will_sop,
    'divorce': divorce_sop,
    'marital': marital_sop,
}


def generate_family_doc(subtype, data=None, output_path=None, title=None):
    """Generate family document via content_blocks + create_document.

    Args:
        subtype: 'will' | 'divorce' | 'marital' | 'support-gift' | 'guardianship'
        data: dict with collected data
        output_path: optional output path
        title: optional document title

    Returns:
        Document object
    """
    if data is None:
        data = {}

    sop = SOP_MAP.get(subtype)
    if sop:
        content_blocks = sop(data)
    else:
        content_blocks = [
            {'type': 'body', 'text': f'子类型: {subtype}'}
        ]

    doc_title = title or {
        'will': '遗 嘱',
        'divorce': '离婚协议书',
        'marital': '夫妻财产协议书',
    }.get(subtype, '婚姻家庭与继承文书')

    create_document(content_blocks, output_path=output_path, title=doc_title)
    return output_path


def main():
    parser = argparse.ArgumentParser(description='婚姻家庭与继承文书生成器')
    parser.add_argument('--subtype', required=True, choices=list(SOP_MAP.keys()),
                        help='子类型')
    parser.add_argument('--title', default='',
                        help='文书标题')
    parser.add_argument('--output', required=True,
                        help='输出路径')
    parser.add_argument('--data', default='{}',
                        help='JSON格式的采集数据')
    args = parser.parse_args()

    data = json.loads(args.data)
    title = args.title or None
    generate_family_doc(args.subtype, data, output_path=args.output, title=title)


if __name__ == '__main__':
    main()
