# 回复邮件模板

Agent 回复邮件时可参考以下模板结构。

---

## 标准回复

```
收件人: {{sender_email}}
主题: Re: {{original_subject}}

{{agent_name}} 已收到您的邮件，处理结果如下：

## 处理摘要
{{summary}}

## 详细结果
{{details}}

---
此邮件由 AI Agent ({{agent_email}}) 自动发送
```

## 通知邮件

```
收件人: {{recipient_email}}
主题: [通知] {{notification_title}}

{{notification_body}}

---
此邮件由 AI Agent ({{agent_email}}) 自动发送
```
