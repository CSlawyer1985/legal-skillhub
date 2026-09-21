#!/usr/bin/env node
// Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
/**
 * 上传宝玉卡片图片到微信 CDN，并插入到草稿中
 */

const fs = require("fs");
const path = require("path");
const axios = require("axios");
const FormData = require("form-data");

// 加载 .env
const envPath = path.join(__dirname, ".env");
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

const APP_ID = process.env.WECHAT_APP_ID;
const APP_SECRET = process.env.WECHAT_APP_SECRET;
const AUTHOR = process.env.WECHAT_AUTHOR;
const THUMB_MEDIA_ID = process.env.WECHAT_THUMB_MEDIA_ID;

const IMAGE_PATH = process.env.IMAGE_PATH || "<你的封面图片绝对路径>";
const DRAFT_TITLE = process.env.DRAFT_TITLE || "<你的文章标题>";

async function main() {
  // 1. 获取 access_token
  console.log("🔑 获取 access_token...");
  const tokenRes = await axios.get("https://api.weixin.qq.com/cgi-bin/token", {
    params: { grant_type: "client_credential", appid: APP_ID, secret: APP_SECRET },
  });
  if (tokenRes.data.errcode) {
    throw new Error(`获取 token 失败: ${tokenRes.data.errmsg}`);
  }
  const accessToken = tokenRes.data.access_token;
  console.log("✅ token 获取成功");

  // 2. 上传图片��微信 CDN
  console.log("☁️  上传图片到微信 CDN...");
  const form = new FormData();
  form.append("media", fs.createReadStream(IMAGE_PATH));
  const uploadRes = await axios.post(
    `https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=${accessToken}`,
    form,
    { headers: form.getHeaders() }
  );
  if (uploadRes.data.errcode) {
    throw new Error(`上传图片失败: ${uploadRes.data.errmsg}`);
  }
  const cdnUrl = uploadRes.data.url;
  console.log(`✅ 图片已上传: ${cdnUrl}`);

  // 3. 查找已有草稿
  console.log("🔍 查找已���草稿...");
  let foundMediaId = null;
  let foundIndex = 0;
  let offset = 0;

  while (true) {
    const draftRes = await axios.post(
      `https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=${accessToken}`,
      { offset, count: 20, no_content: 0 },
      { timeout: 10000 }
    );
    const items = draftRes.data.item || [];
    for (const item of items) {
      const newsItems = item.content && item.content.news_item;
      if (!newsItems) continue;
      for (let i = 0; i < newsItems.length; i++) {
        if (newsItems[i].title === DRAFT_TITLE) {
          foundMediaId = item.media_id;
          foundIndex = i;
          break;
        }
      }
      if (foundMediaId) break;
    }
    if (foundMediaId || items.length < 20) break;
    offset += 20;
  }

  if (!foundMediaId) {
    throw new Error("未找到目标草稿");
  }
  console.log(`✅ 找到草稿 media_id: ${foundMediaId}`);

  // 4. 获取当前草稿内容
  console.log("📄 获取当前草稿内容...");
  const getDraftRes = await axios.post(
    `https://api.weixin.qq.com/cgi-bin/draft/get?access_token=${accessToken}`,
    { media_id: foundMediaId },
    { timeout: 10000 }
  );

  const newsItem = getDraftRes.data.news_item[foundIndex];
  // 注意：content 字段不存在时的处理
  const currentContent = newsItem.content || "";

  // 5. 在正文最前面插入图片 HTML
  const imgHtml = `<p style="text-align:center;margin:13px 0;line-height:2.0;"><img src="${cdnUrl}" style="max-width:100%;display:inline-block;border-radius:8px;" /></p>`;
  const newContent = imgHtml + currentContent;

  console.log("📝 更新草稿（插入图片）...");

  // 6. 删除旧草稿，重新创建
  // 先删除
  const deleteRes = await axios.post(
    `https://api.weixin.qq.com/cgi-bin/draft/delete?access_token=${accessToken}`,
    { media_id: foundMediaId },
    { timeout: 10000 }
  );
  if (deleteRes.data.errcode) {
    throw new Error(`删除旧草稿失败: ${deleteRes.data.errmsg}`);
  }
  console.log("✅ 旧草稿已删除");

  // 重新创建
  const createBody = {
    articles: [{
      title: DRAFT_TITLE,
      author: AUTHOR,
      digest: newsItem.digest || "",
      content: newContent,
      thumb_media_id: THUMB_MEDIA_ID,
      need_open_comment: 1,
      only_fans_can_comment: 0,
      show_cover_pic: 0,
    }],
  };

  const createRes = await axios.post(
    `https://api.weixin.qq.com/cgi-bin/draft/add?access_token=${accessToken}`,
    createBody,
    { timeout: 30000 }
  );

  if (createRes.data.errcode) {
    throw new Error(`创建草稿失败 [${createRes.data.errcode}]: ${createRes.data.errmsg}`);
  }

  console.log(`✅ 草稿已更新！`);
  console.log(`   标题: ${DRAFT_TITLE}`);
  console.log(`   新 media_id: ${createRes.data.media_id}`);
  console.log(`   图片 CDN: ${cdnUrl}`);
  console.log(`   请登录公众号后台查看: https://mp.weixin.qq.com/cgi-bin/appmsg`);
}

main().catch((err) => {
  console.error(`❌ 失败: ${err.message}`);
  process.exit(1);
});
