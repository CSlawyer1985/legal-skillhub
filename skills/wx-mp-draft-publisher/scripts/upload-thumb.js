#!/usr/bin/env node
// Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
/**
 * 上传封面图到微信并保存 media_id 到 .env
 */

const fs = require("fs");
const path = require("path");
const os = require("os");
const axios = require("axios");
const FormData = require("form-data");

// 加载配置
function loadConfig() {
  const envPath = path.join(__dirname, ".env");
  if (fs.existsSync(envPath)) {
    const lines = fs.readFileSync(envPath, "utf-8").split("\n");
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const eqIdx = trimmed.indexOf("=");
      if (eqIdx === -1) continue;
      const key = trimmed.slice(0, eqIdx).trim();
      const val = trimmed.slice(eqIdx + 1).trim().replace(/^["']|["']$/g, "");
      if (!process.env[key]) process.env[key] = val;
    }
  }
  return {
    appId: process.env.WECHAT_APP_ID || "",
    appSecret: process.env.WECHAT_APP_SECRET || "",
  };
}

async function uploadThumb(imagePath) {
  const config = loadConfig();

  if (!config.appId || !config.appSecret) {
    throw new Error("缺少 WECHAT_APP_ID 或 WECHAT_APP_SECRET");
  }

  // 1. 获取 access_token
  console.log("🔑 正在获取微信 access_token...");
  const tokenRes = await axios.get("https://api.weixin.qq.com/cgi-bin/token", {
    params: {
      grant_type: "client_credential",
      appid: config.appId,
      secret: config.appSecret,
    },
  });

  if (tokenRes.data.errcode) {
    throw new Error(`获取 access_token 失败: ${tokenRes.data.errmsg}`);
  }
  const accessToken = tokenRes.data.access_token;
  console.log("✅ 获取 access_token 成功");

  // 2. 上传图片为永久素材（thumb）
  console.log(`🖼️  正在上传封面图: ${path.basename(imagePath)}`);
  const form = new FormData();
  form.append("media", fs.createReadStream(imagePath));

  const res = await axios.post(
    `https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=${accessToken}&type=thumb`,
    form,
    { headers: form.getHeaders(), timeout: 15000 }
  );

  if (res.data.errcode) {
    throw new Error(`上传封面失败 [${res.data.errcode}]: ${res.data.errmsg}`);
  }

  const thumbMediaId = res.data.media_id;
  console.log(`✅ 封面图上传成功`);
  console.log(`   media_id: ${thumbMediaId}`);

  // 3. 保存到 .env 文件
  const envPath = path.join(__dirname, ".env");
  let envContent = "";
  if (fs.existsSync(envPath)) {
    envContent = fs.readFileSync(envPath, "utf-8");
  }

  // 更新或添加 WECHAT_THUMB_MEDIA_ID
  const lines = envContent.split("\n");
  let found = false;
  const newLines = lines.map(line => {
    if (line.startsWith("WECHAT_THUMB_MEDIA_ID=")) {
      found = true;
      return `WECHAT_THUMB_MEDIA_ID=${thumbMediaId}`;
    }
    return line;
  });

  if (!found) {
    newLines.push(`WECHAT_THUMB_MEDIA_ID=${thumbMediaId}`);
  }

  fs.writeFileSync(envPath, newLines.join("\n"), "utf-8");
  console.log(`💾 已保存到 .env: WECHAT_THUMB_MEDIA_ID=${thumbMediaId}`);

  return thumbMediaId;
}

// 主流程
async function main() {
  const imagePath = process.argv[2];
  if (!imagePath) {
    console.error("用法: node upload-thumb.js <图片路径>");
    process.exit(1);
  }

  if (!fs.existsSync(imagePath)) {
    console.error(`文件不存在: ${imagePath}`);
    process.exit(1);
  }

  try {
    await uploadThumb(imagePath);
  } catch (err) {
    console.error(`❌ 失败: ${err.message}`);
    process.exit(1);
  }
}

main();
