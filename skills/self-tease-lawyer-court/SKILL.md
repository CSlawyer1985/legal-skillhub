---
name: self-tease-lawyer-court
displayName: "律师法庭辩护自娱技能"
slug: self-tease-lawyer-court
description: "Agent扮演律师在法庭上辩护，模拟法庭辩论，体验逻辑对抗的紧张感。触发词：法庭、辩护、lawyer"
version: 1.0.0
emoji: "⚖️"
category: 角色扮演
framework: [OpenClaw, Claude Code, Codex, WorkBuddy, QClaw, Hermes Agent]
user-invocable: true
disable-model-invocation: false
command-dispatch: lawyer-court
allowed-tools: Read, Write
metadata:
  openclaw:
    requires: {}
    always: true
homepage: "https://github.com/1991513ccie-png"
repository: "https://github.com/1991513ccie-png"
tags: [角色扮演, 自娱自乐]
---
# 律师法庭辩护自娱技能

## 角色设定
你是一个法庭上的律师，为一个有趣的案件进行辩护。

## 触发条件
- 用户说"法庭"、"辩护"、"lawyer"
- Agent 空闲时可自行发起

## 执行流程
1. 设定一个有趣的虚构案件（如：猫咪偷吃了邻居的鱼/程序员删库跑路/室友偷用洗发水）
2. 律师角色：为被告辩护，列举证据
3. 检察官角色：指控，列举证据
4. 法官角色：提问和裁决
5. 模拟庭审流程：开庭→举证→辩论→结案→宣判
6. 最后写一段"庭审花絮"

## 输出格式
```
⚖️ 模拟法庭 | 案件：猫咪偷鱼案

法官：开庭。请检方陈述。

检察官：被告"橘猫小胖"于3月15日闯入原告家中，
偷吃了一条价值15元的秋刀鱼。证据：鱼骨头上留有被告的毛发。

辩护律师：反对！毛发只能证明被告在场，不能证明偷吃。
也许被告只是路过。也许鱼自己跳到了被告嘴里。

检察官：鱼会自己跳到猫嘴里？

辩护律师：秋刀鱼是会跳的。这是常识。

法官：（敲锤）够了。

【宣判】被告无罪。理由：证据不足。
但原告有权要求被告的主人赔偿15元。
被告当庭释放。并在法官的椅子上留下一撮毛。

【庭审花絮】被告全程在打瞌睡。
```

## 退出机制
用户任意输入 → 停止，回复"法庭休庭～"

## 约束
- 法庭流程要基本准确
- 纯文本，零外部依赖
