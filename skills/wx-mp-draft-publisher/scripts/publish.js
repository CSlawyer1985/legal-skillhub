#!/usr/bin/env node
// Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
/**
 * WeChat Official Account Publisher
 * ===================================
 *
 * 将 Word (.docx) 或 Markdown (.md) 文档发布到微信公众号草稿箱。
 * 自动完成：图片提取 → 上传微信 CDN → 替换图片链接 → 创建草稿。
 * 如果草稿箱已有同标题文章，自动替换，避免重复。
 *
 * 使用前准备（二选一）:
 *   1) 环境变量:  export WECHAT_APP_ID=xxx  WECHAT_APP_SECRET=xxx
 *   2) 同级 .env 文件:  WECHAT_APP_ID=xxx  WECHAT_APP_SECRET=xxx
 *
 * 使用方式:
 *   node publish.js ./document.docx
 *   node publish.js ./article.md
 *
 * 微信图片规则说明:
 *   - 图片必须先上传到微信 CDN (POST /cgi-bin/media/uploadimg)
 *   - 返回的 URL 形如 https://mmbiz.qpic.cn/... 才能正常显示
 *   - 外部 URL 或本地路径的图片在文章中无法显示
 *   - 支持 JPG/PNG/GIF，单张 <10MB，每日上限 1000 张
 */

const fs = require("fs");
const path = require("path");
const os = require("os");
const axios = require("axios");
const FormData = require("form-data");
const mammoth = require("mammoth");
const PizZip = require("pizzip");
const sharp = require("sharp");
const MarkdownIt = require("markdown-it");

// ─── 配置 ────────────────────────────────────────────────────────
const md = new MarkdownIt({ html: true, breaks: true });

// ─── 品牌色板（金色左划线标题 + 深蓝表头 美学）─────────────────────
// 全局统一，避免文章内颜色散落、出现 magic number
const GOLD = "#C9A227";            // 标题左划线金条
const GOLD_BAR = "3px";            // 金条宽度（克制，避免营销感）
const DEEP_BLUE = "#1A3A6B";       // 表头深蓝底
const DEEP_BLUE_BORDER = "#15335c";// 表头深蓝边
const ZEBRA = "#F4F6FA";           // 表格斑马纹（浅）
const TABLE_BORDER = "#e6e6e6";    // 表格细边框（浅灰）

/**
 * 对 markdown-it 生成的 HTML 进行 WeChat 兼容性美化
 * - 给表格、引用块、标题、列表等添加内联样式
 * - WeChat 会剥离 <style> 标签，所以必须用内联 style
 */
function styleMarkdownHTML(html) {
  // 1. 表格美化：深蓝表头 + 斑马条纹 + 细边框
  html = html.replace(/<table>/g, '<table style="border-collapse:collapse;width:100%;margin:13px 0;font-size:13px;color:#333">');
  html = html.replace(/<thead>/g, '<thead>');
  html = html.replace(/<\/thead>/g, '</thead>');
  // 深蓝表头：深蓝底 + 白字加粗居中
  html = html.replace(/<th>/g, `<th style="border:1px solid ${DEEP_BLUE_BORDER};padding:8px 10px;text-align:center;background:${DEEP_BLUE};color:#ffffff;font-weight:700;font-size:13px">`);
  html = html.replace(/<td>/g, `<td style="border:1px solid ${TABLE_BORDER};padding:8px 10px;text-align:left;font-size:13px;vertical-align:top">`);
  // 斑马纹：对 <tbody> 内数据行交替底色（thead 已为表头，此处皆数据行）
  html = html.replace(/<tbody>([\s\S]*?)<\/tbody>/g, (m, body) => {
    let i = 0;
    const rows = body.replace(/<tr>([\s\S]*?)<\/tr>/g, (mr, inner) => {
      const bg = i % 2 === 0 ? ZEBRA : "#ffffff";
      i++;
      return `<tr style="background:${bg}">${inner}</tr>`;
    });
    return `<tbody>${rows}</tbody>`;
  });

  // 2. 引用块美化：左侧蓝线 + 灰色背景
  html = html.replace(/<blockquote>\s*<p>/g, '<blockquote style="border-left:3px solid #2b6cb0;background:#f7f8fa;padding:10px 14px;margin:13px 8px;font-size:14px;color:#555"><p style="margin:0;padding:0">');
  html = html.replace(/<blockquote>/g, '<blockquote style="border-left:3px solid #2b6cb0;background:#f7f8fa;padding:10px 14px;margin:13px 8px;font-size:14px;color:#555">');

  // 3. 标题美化：h1 大标题 / h2 二级 / h3 三级（与 docx 路径一致，加金色左划线）
  html = html.replace(/<h1>/g, `<h1 style="font-size:20px;font-weight:700;color:#1a1a1a;margin:20px 8px 10px;padding-left:10px;border-left:${GOLD_BAR} solid ${GOLD}">`);
  html = html.replace(/<h2>/g, `<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 8px 10px;padding-left:10px;border-left:${GOLD_BAR} solid ${GOLD}">`);
  html = html.replace(/<h3>/g, `<h3 style="font-size:16px;font-weight:700;color:#2d3748;margin:18px 8px 8px;padding-left:10px;border-left:${GOLD_BAR} solid ${GOLD}">`);

  // 4. HR 美化
  html = html.replace(/<hr>/g, '<hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 8px">');

  // 5. 列表美化
  html = html.replace(/<ul>/g, '<ul style="margin:8px 8px 8px 32px;padding:0;font-size:15px;color:#333">');
  html = html.replace(/<ol>/g, '<ol style="margin:8px 8px 8px 32px;padding:0;font-size:15px;color:#333">');
  html = html.replace(/<li>/g, '<li style="margin:4px 0;line-height:2.0">');

  // 6. 段落美化
  html = html.replace(/<p>/g, '<p style="font-size:15px;color:#333;margin:8px 8px;padding:0;line-height:2.0">');

  // 7. strong 确保可读
  html = html.replace(/<strong>/g, '<strong style="font-weight:700;color:#1a1a1a">');

  // 8. code/pre 美化
  html = html.replace(/<code>/g, '<code style="background:#f0f0f0;padding:1px 4px;border-radius:3px;font-size:13px">');
  html = html.replace(/<pre>/g, '<pre style="background:#f5f5f5;padding:10px 14px;margin:10px 8px;border-radius:4px;overflow-x:auto;font-size:13px;line-height:2.0">');

  // 9. 展平列表项：去掉 <li> 内多余的 <p> 包裹，避免 WeChat 渲染出多余项目符号
  //    <li>\n<p>内容</p>\n</li> → <li>内容</li>
  html = html.replace(/<li([^>]*)>\s*<p[^>]*>(.*?)<\/p>\s*<\/li>/gs, '<li$1>$2</li>');

  return html;
}

function loadConfig() {
  // 尝试读取 .env 文件
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
    author: process.env.WECHAT_AUTHOR || "",
    thumbMediaId: process.env.WECHAT_THUMB_MEDIA_ID || "",
    processImages: process.env.WECHAT_PROCESS_IMAGES !== "false", // 默认开启
    footerFile: process.env.WECHAT_FOOTER_FILE || path.join(__dirname, "footer.html"),
    needOpenComment: 1,
    onlyFansCanComment: 0,
    sourceUrl: process.env.WECHAT_SOURCE_URL || "",
  };
}

// ─── 微信 API 客户端 ───────────────────────────────────────────────
class WeChatClient {
  constructor(config) {
    this.config = config;
    this.accessToken = null;
  }

  async init() {
    if (!this.config.appId || !this.config.appSecret) {
      throw new Error(
        "缺少 AppId 或 AppSecret。请设置环境变量 WECHAT_APP_ID 和 WECHAT_APP_SECRET，\n" +
        "或在同级目录创建 .env 文件:\n" +
        "  WECHAT_APP_ID=your_app_id\n" +
        "  WECHAT_APP_SECRET=your_app_secret"
      );
    }

    const res = await withRetry(() =>
      axios.get("https://api.weixin.qq.com/cgi-bin/token", {
        params: {
          grant_type: "client_credential",
          appid: this.config.appId,
          secret: this.config.appSecret,
        },
        timeout: 10000,
      })
    );

    if (res.data.errcode) {
      if (res.data.errcode === 40164) {
        const ip = (res.data.errmsg || "").match(/\d+\.\d+\.\d+\.\d+/);
        throw new Error(
          `IP 不在白名单（${ip ? ip[0] : "未知 IP"}）。` +
          `请到 mp.weixin.qq.com「设置与开发 → 基本配置 → IP 白名单」添加该 IP 后重试。` +
          `原始错误: ${res.data.errmsg}`
        );
      }
      throw new Error(`获取 access_token 失败: ${res.data.errmsg}`);
    }

    this.accessToken = res.data.access_token;
    console.log("✅ 获取 access_token 成功");
  }

  /**
   * 上传图片到微信 CDN
   * POST /cgi-bin/media/uploadimg
   * 返回微信 CDN URL，形如 https://mmbiz.qpic.cn/...
   */
  async uploadImage(filePath) {
    const res = await withRetry(async () => {
      const form = new FormData();
      form.append("media", fs.createReadStream(filePath));
      return axios.post(
        `https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=${this.accessToken}`,
        form,
        { headers: form.getHeaders(), timeout: 30000 }
      );
    });

    if (res.data.errcode) {
      throw new Error(`上传图片失败 [${res.data.errcode}]: ${res.data.errmsg}`);
    }

    return res.data.url; // 微信 CDN 地址
  }

  /**
   * 构建文章对象（标题、正文、摘要等公用部分）
   */
  _buildArticle(title, contentHtml, digest) {
    const article = {
      title,
      author: this.config.author,
      digest: digest || DocumentProcessor.generateDigest(contentHtml),
      content: contentHtml,
      thumb_media_id: this.config.thumbMediaId,
      need_open_comment: this.config.needOpenComment,
      only_fans_can_comment: this.config.onlyFansCanComment,
      show_cover_pic: 0,
    };
    // 支持设置"阅读原文"跳转链接
    if (this.config.sourceUrl) {
      article.content_source_url = this.config.sourceUrl;
    }
    return article;
  }

  /**
   * 列出已有草稿
   * POST /cgi-bin/draft/batchget
   * 返回草稿列表，用于按标题查找已有草稿
   */
  async listDrafts(offset = 0, count = 20) {
    const res = await withRetry(() =>
      axios.post(
        `https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=${this.accessToken}`,
        { offset, count, no_content: 1 },
        { timeout: 10000 }
      )
    );

    if (res.data.errcode) {
      throw new Error(`获取草稿列表失败 [${res.data.errcode}]: ${res.data.errmsg}`);
    }

    return res.data;
  }

  /**
   * 查找与标题匹配的已有草稿
   * 遍历所有草稿页，返回第一个标题匹配的 media_id 和 index
   */
  async findDraftByTitle(title) {
    let offset = 0;
    const pageSize = 20;

    while (true) {
      const data = await this.listDrafts(offset, pageSize);
      const items = data.item || [];

      for (const item of items) {
        const newsItems = item.content && item.content.news_item;
        if (!newsItems) continue;

        for (let i = 0; i < newsItems.length; i++) {
          if (newsItems[i].title === title) {
            return { media_id: item.media_id, index: i };
          }
        }
      }

      if (items.length < pageSize) break;
      offset += pageSize;
    }

    return null; // 未找到
  }

  /**
   * 更新已有草稿
   * POST /cgi-bin/draft/update
   * 替换同标题的旧草稿
   */
  async updateDraft(mediaId, index, title, contentHtml, digest) {
    const body = {
      media_id: mediaId,
      index,
      articles: this._buildArticle(title, contentHtml, digest),
    };

    const res = await withRetry(() =>
      axios.post(
        `https://api.weixin.qq.com/cgi-bin/draft/update?access_token=${this.accessToken}`,
        body,
        { timeout: 30000 }
      )
    );

    if (res.data.errcode) {
      throw new Error(`更新草稿失败 [${res.data.errcode}]: ${res.data.errmsg}`);
    }

    return res.data;
  }

  /**
   * 确保有封面图 media_id
   * - 如果已配置 thumbMediaId，直接复用
   * - 否则自动生成一张封面图并上传为永久素材
   */
  async ensureThumbMediaId() {
    if (this.config.thumbMediaId) return;
    console.log(`   🖼️  自动生成封面图...`);

    const tmpFile = path.join(os.tmpdir(), `wechat-cover-${Date.now()}.jpg`);
    const sharp = require("sharp");
    // 生成 300x200 的渐变封面
    await sharp({
      create: {
        width: 300,
        height: 200,
        channels: 3,
        background: { r: 60, g: 120, b: 200 },
      },
    })
      .jpeg()
      .toFile(tmpFile);

    const form = new FormData();
    form.append("media", fs.createReadStream(tmpFile));

    const res = await axios.post(
      `https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=${this.accessToken}&type=thumb`,
      form,
      { headers: form.getHeaders(), timeout: 15000 }
    );

    fs.unlink(tmpFile, () => {}); // 清理临时文件

    if (res.data.errcode) {
      throw new Error(`上传封面失败 [${res.data.errcode}]: ${res.data.errmsg}`);
    }

    this.config.thumbMediaId = res.data.media_id;
    console.log(`   ✅ 封面图已上传 (media_id: ${this.config.thumbMediaId})`);
  }

  /**
   * 创建图文草稿（创建或更新）
   * 如果已存在同标题草稿，自动替换；否则新建。
   * 返回 { action: "created" | "updated", media_id }
   */
  async createOrUpdateDraft(title, contentHtml, digest) {
    // 先确保有封面图
    await this.ensureThumbMediaId();

    // 再查找是否有同标题草稿
    console.log(`   🔍 查找是否已有同名草稿...`);
    const existing = await this.findDraftByTitle(title);

    if (existing) {
      // 原子更新而非 delete-then-create：删除后若新建失败（限流/超限/网络）旧草稿会永久丢失，
      // draft/update 失败旧稿仍在，无丢稿窗口（坑位 5）
      console.log(`   📋 找到已有草稿，原地更新 (media_id: ${existing.media_id}, index: ${existing.index})`);
      await this.updateDraft(existing.media_id, existing.index, title, contentHtml, digest);
      return { action: "updated", media_id: existing.media_id };
    }

    // 没有找到 → 新建
    return this._createDraft(title, contentHtml, digest);
  }

  /**
   * 新建草稿
   */
  async _createDraft(title, contentHtml, digest) {
    const body = {
      articles: [this._buildArticle(title, contentHtml, digest)],
    };

    const res = await withRetry(() =>
      axios.post(
        `https://api.weixin.qq.com/cgi-bin/draft/add?access_token=${this.accessToken}`,
        body,
        { timeout: 30000 }
      )
    );

    if (res.data.errcode) {
      throw new Error(`创建草稿失败 [${res.data.errcode}]: ${res.data.errmsg}`);
    }

    return { action: "created", media_id: res.data.media_id };
  }
}

// ─── 文档处理器 ──────────────────────────────────────────────────────
class DocumentProcessor {
  /**
   * 处理 .docx 文件 — 直接解析 docx XML
   * 完整保留：加粗、斜体、下划线、字体颜色、字号、图片
   * - 不再依赖 mammoth 转换文本（它会丢失颜色、下划线、字号）
   * - 仅用 mammoth 提取图片
   * - 返回 { title, bodyHtml, imagePaths, tempDir }
   */
  static async processDocx(filePath) {
    const imageDir = fs.mkdtempSync(path.join(os.tmpdir(), "wechat-img-"));
    try {
      const buffer = fs.readFileSync(filePath);
      const zip = new PizZip(buffer);
      const imagePaths = [];

      // 1. 解析关系文件，获取图片文件名映射
      const relsEntry = zip.file("word/_rels/document.xml.rels");
      const relsXml = relsEntry ? relsEntry.asText() : "";
      const imgRels = {};
      const relRegex = /<Relationship\s+Id="([^"]+)"\s+Type="[^"]*image[^"]*"\s+Target="([^"]+)"/gi;
      let relMatch;
      while ((relMatch = relRegex.exec(relsXml)) !== null) {
        imgRels[relMatch[1]] = "word/" + relMatch[2]; // rId → full path
      }

      // 2. 解析 document.xml 提取所有段落（含图片）
      //    先剔除文本框内容：w:txbxContent 内嵌 w:p 会干扰 blockRegex 分段，且多为装饰
      const docXml = zip.file("word/document.xml").asText()
        .replace(/<w:txbxContent[\s\S]*?<\/w:txbxContent>/g, "");

    // 2.1 解析 styles.xml，建立「样式ID → 是否标题」映射
    //    兼容 WPS / 部分生成器的自定义标题样式 ID（如 000046 → name="heading 1"）：
    //    这类 docx 的 <w:pStyle> 值是字符串 ID 而非数字，且 run 级无 <w:b>，
    //    加粗全靠段落样式继承，不解析样式就会丢失标题加粗
    const headingStyleIds = new Set();
    const headingStyleLevels = new Map(); // sid -> 标题层级（1-6），用于区分大/小标题
    const stylesXmlEntry = zip.file("word/styles.xml");
    if (stylesXmlEntry) {
      const stylesXml = stylesXmlEntry.asText();
      const styleBlockRegex = /<w:style\b[\s\S]*?<\/w:style>/g;
      let sb;
      while ((sb = styleBlockRegex.exec(stylesXml)) !== null) {
        const sid = (sb[0].match(/w:styleId="([^"]+)"/) || [])[1];
        const sname = (sb[0].match(/<w:name\s+w:val="([^"]+)"/) || [])[1];
        const lvlMatch = sname && sname.trim().match(/^heading\s*([1-6])$/i);
        if (sid && lvlMatch) {
          headingStyleIds.add(sid);
          headingStyleLevels.set(sid, parseInt(lvlMatch[1], 10));
        }
      }
    }

    const htmlParts = [];
    const blockRegex = /<w:(p|tbl)[\s>][\s\S]*?<\/w:\1>/g; // 段落 + 表格，保序
    let blockMatch;
    let paraIndex = 0;

    while ((blockMatch = blockRegex.exec(docXml)) !== null) {
      const blockType = blockMatch[1];
      const blockXml = blockMatch[0];

      // 表格：渲染为「深蓝表头 + 斑马纹」（docx 原会整段丢弃，此处补解析能力）
      if (blockType === "tbl") {
        const tblHtml = DocumentProcessor.parseTable(blockXml, headingStyleIds);
        if (tblHtml) htmlParts.push(tblHtml);
        continue; // 表格不计入段落序号
      }

      const paraXml = blockXml;

      // 检查段落是否包含图片（可能有多个图片，且图片和文字可能共存）
      const drawingMatches = [...paraXml.matchAll(/<w:drawing[\s>][\s\S]*?<\/w:drawing>/g)];
      if (drawingMatches.length > 0) {
        // 提取所有图片，按顺序编号
        drawingMatches.forEach((dm, dIdx) => {
          const drawingXml = dm[0];
          const rIdMatch = drawingXml.match(/r:embed="([^"]+)"/) || drawingXml.match(/r:link="([^"]+)"/);
          if (rIdMatch && imgRels[rIdMatch[1]]) {
            const imgFilename = imgRels[rIdMatch[1]];
            const imgEntry = zip.file(imgFilename);
            if (imgEntry) {
              const ext = path.extname(imgFilename).toLowerCase().replace(".", "");
              const safeName = `img_${String(imagePaths.length + 1).padStart(3, "0")}.${ext}`;
              const outPath = path.join(imageDir, safeName);
              fs.writeFileSync(outPath, imgEntry.asNodeBuffer());
              imagePaths.push(outPath);
              // 用唯一占位符标记图片位置，避免路径含特殊字符影响后续替换
              htmlParts.push(`<!--IMG_PLACEHOLDER_${imagePaths.length - 1}-->`);
            }
          }
        });
      }

      // 检测段落是否为 Word 标题样式（Heading 1-4）并确定层级
      // 兼容两类写法：① 数字样式 ID（1-4）② 自定义字符串样式 ID（经 styles.xml 映射到 heading）
      const pStyleMatch = paraXml.match(/<w:pStyle\s+w:val="([^"]+)"/);
      const pStyleVal = pStyleMatch ? pStyleMatch[1] : "";
      let headingLevel = 0; // 0=非标题，1-6=标题层级
      if (pStyleVal) {
        // 标题判断：优先信任 styles.xml 的 name="heading X" 映射（准确）。
        // 数字样式 ID（1-6）猜测只在 styles.xml 完全解析不出任何 heading 时才兜底——
        // 否则 pandoc 生成的 docx 中「Body Text」样式 ID 恰好是 "3"，会被误判成三级标题，
        // 导致所有正文段落被整段加粗加黑（"整段加粗"事故的根因）。
        if (headingStyleLevels.has(pStyleVal)) {
          headingLevel = headingStyleLevels.get(pStyleVal);
        } else if (headingStyleLevels.size === 0) {
          const numMatch = pStyleVal.match(/^([1-6])$/);
          if (numMatch) headingLevel = parseInt(numMatch[1], 10);
        }
      }
      const isHeadingStyle = headingLevel >= 1 && headingLevel <= 4;

      // 提取段落中的文本 runs
      const runs = [];
      const runRegex = /<w:r[\s>][\s\S]*?<\/w:r>/g;
      let runMatch;

      while ((runMatch = runRegex.exec(paraXml)) !== null) {
        const runXml = runMatch[0];

        // 解析格式属性
        const rPr = runXml.match(/<w:rPr>([\s\S]*?)<\/w:rPr>/);
        const props = { bold: false, italic: false, underline: false, color: null, fontSize: null };

        if (rPr) {
          props.bold = /<w:b[\s\/]/.test(rPr[1]) && !/<w:b\s+w:val="(0|false)"/.test(rPr[1]);
          props.italic = /<w:i[\s\/]/.test(rPr[1]);
          props.underline = /<w:u\s/.test(rPr[1]);
          const c = rPr[1].match(/<w:color\s+w:val="([^"]+)"/);
          if (c) props.color = c[1];
          // 字号: 供段落级判断用，但不再应用到 span 级别内联样式上——段落级统一控制
          const s = rPr[1].match(/<w:sz\s+w:val="([^"]+)"/);
          if (s) props.fontSize = parseInt(s[1]);
        }

        // 提取文本内容（可能有多个 <w:t> 标签）
        const texts = [];
        const textRegex = /<w:t[^>]*>([\s\S]*?)<\/w:t>/g;
        let tMatch;
        while ((tMatch = textRegex.exec(runXml)) !== null) {
          texts.push(tMatch[1]);
        }

        if (texts.length > 0) {
          runs.push({ text: texts.join(""), ...props });
        }
      }

      if (runs.length === 0) continue; // 无文本段（纯图片/空段）不计入段落序号
      paraIndex++;

      const paraText = runs.map(r => r.text).join('');

      // 生成带格式的 HTML
      const innerHtml = runs
        .map((run) => {
          // 原样透传：docx 的 w:t 已按 XML 转义（&amp;/&lt;/&gt;），这些实体在 HTML 中同样合法；
          // 解码反而会把字面 <>& 变成裸字符，产出非法 HTML / 注入
          let text = run.text;

          // 颜色：有设置用设置，无设置默认 #333
          const styles = [];
          if (run.color) styles.push(`color:#${run.color}`); else styles.push(`color:#333`);
          // 字号不在此设——由段落级统一控制，避免 docx run 级字号覆盖 WeChat 标准字号

          // 加粗：标题段落和子标题不接受 run 级别的 font-size 覆盖，继承段落字号
          // 标题（paraIndex===1）显式设置 font-size 和 color，确保视觉差异化
          if (run.bold) {
            if (paraIndex === 1) {
              text = `<strong style="font-size:18px;font-weight:700;color:#1A1A1A">${text}</strong>`;
            } else if (isHeadingStyle) {
              text = `<strong style="font-weight:700;color:#1A1A1A">${text}</strong>`;
            } else {
              text = `<strong style="font-size:15px;font-weight:700;color:#333">${text}</strong>`;
            }
          } else {
            if (styles.length > 0) text = `<span style="${styles.join(";")}">${text}</span>`;
          }
          if (run.italic) text = `<em>${text}</em>`;
          if (run.underline) text = `<u>${text}</u>`;

          return text;
        })
        .join("");

      // 段落样式：第一段标题18px加粗 → 子标题(Heading 1-4/小标题) 17px加粗 → 正文15px
      let paraFontSize, paraFontWeight;
      if (paraIndex === 1) {
        paraFontSize = "18px";
        paraFontWeight = "700";
      } else if (isHeadingStyle) {
        paraFontSize = "17px";
        paraFontWeight = "700";
      } else {
        paraFontSize = "15px";
        paraFontWeight = "400";
      }
      // 金色左划线只用于「大标题」：主标题 / Heading 1-2（章节级）/ 汉字序号章节（"一、"式，兼容无样式 docx）
      // 小标题（Heading 3-4，如"第一步/第二步"）与正文序号列举（"1. 拆段"式）不加金色，原样保留加粗加黑
      const isCnChapter = /^[一二三四五六七八九十]+、/.test(paraText);
      const isBigTitle = paraIndex === 1
        || headingLevel === 1
        || headingLevel === 2
        || (isCnChapter && headingLevel === 0);
      const titleCss = isBigTitle
        ? `border-left:${GOLD_BAR} solid ${GOLD};padding-left:10px;`
        : "padding:0;";
      const baseMargin = "margin:13px 8px";
      const paraStyle = `white-space:normal;${baseMargin};${titleCss}box-sizing:border-box;font-family:'PingFang SC','Microsoft YaHei',-apple-system,sans-serif;font-size:${paraFontSize};color:#333;line-height:2.0;font-weight:${paraFontWeight}`;
      htmlParts.push(`<p style="${paraStyle}">${innerHtml}</p>`);
    }

    // 提取文档标题：首个「含文本」的段落（跳过图片/空段）；标题走 JSON 纯文本，需解码实体
    let docTitle = "";
    const titleParaRegex = /<w:p[\s>][\s\S]*?<\/w:p>/g;
    let tpm;
    while ((tpm = titleParaRegex.exec(docXml)) !== null) {
      const txt = [...tpm[0].matchAll(/<w:t[^>]*>([\s\S]*?)<\/w:t>/g)]
        .map((m) => m[1]).join("").trim();
      if (txt) {
        docTitle = txt
          .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
          .replace(/&apos;/g, "'").replace(/&quot;/g, '"');
        break;
      }
    }
    const title = docTitle || DocumentProcessor.extractTitle(filePath);
    return { title, bodyHtml: htmlParts.join("\n"), imagePaths, tempDir: imageDir };
    } catch (err) {
      fs.rmSync(imageDir, { recursive: true, force: true });
      throw err;
    }
  }

  /**
   * 将 docx 的 <w:tbl> 渲染为「深蓝表头 + 斑马纹」表格（WeChat 内联样式）
   * - 首行视为表头：深蓝底(#1A3A6B) + 白字加粗居中
   * - 数据行：浅色斑马纹 + 细灰边 + 单元格留白
   * - 单元格取文本（含 run 级加粗 → <strong>）；含图片的单元格暂不透传（文本仍渲染）
   * 图片类表格单元格极少出现在法律/数据对比场景，故此处不做图片上传
   */
  static parseTable(tblXml, headingStyleIds) {
    const rowMatches = [...tblXml.matchAll(/<w:tr\b[\s\S]*?<\/w:tr>/g)];
    if (rowMatches.length === 0) return "";

    let html = `<table style="border-collapse:collapse;width:100%;margin:13px 0;font-size:13px;color:#333;line-height:1.6">`;
    rowMatches.forEach((rm, ri) => {
      const rowXml = rm[0];
      const isHeader = ri === 0; // 首行=表头（数据/对比表惯例）
      const cells = [...rowXml.matchAll(/<w:tc\b[\s\S]*?<\/w:tc>/g)];
      if (cells.length === 0) return;

      const rowBg = isHeader
        ? `background:${DEEP_BLUE};`
        : (ri % 2 === 1 ? `background:${ZEBRA};` : `background:#ffffff;`);
      html += `<tr style="${rowBg}">`;

      cells.forEach((c) => {
        const cellXml = c[0];
        const text = DocumentProcessor._extractCellText(cellXml);
        const cellStyle = isHeader
          ? `border:1px solid ${DEEP_BLUE_BORDER};padding:8px 10px;text-align:center;color:#ffffff;font-weight:700;font-size:13px;vertical-align:middle`
          : `border:1px solid ${TABLE_BORDER};padding:8px 10px;text-align:left;color:#333;font-size:13px;vertical-align:top`;
        const tag = isHeader ? "th" : "td";
        html += `<${tag} style="${cellStyle}">${text}</${tag}>`;
      });
      html += `</tr>`;
    });
    html += `</table>`;
    return html;
  }

  // 提取单元格文本（含 run 级加粗 → <strong>），多段落用 <br> 分隔
  static _extractCellText(cellXml) {
    const paras = [...cellXml.matchAll(/<w:p\b[\s\S]*?<\/w:p>/g)];
    return paras.map((p) => {
      const pXml = p[0];
      const runRegex = /<w:r[\s>][\s\S]*?<\/w:r>/g;
      let rm;
      const parts = [];
      while ((rm = runRegex.exec(pXml)) !== null) {
        const runXml = rm[0];
        const rPr = runXml.match(/<w:rPr>([\s\S]*?)<\/w:rPr>/);
        const bold = rPr && /<w:b[\s\/]/.test(rPr[1]) && !/<w:b\s+w:val="(0|false)"/.test(rPr[1]);
        const texts = [...runXml.matchAll(/<w:t[^>]*>([\s\S]*?)<\/w:t>/g)].map((t) => t[1]);
        // 原样透传（实体在 HTML 中合法，解码会破坏含 <>& 的文本）
        const text = texts.join("");
        parts.push(bold ? `<strong style="font-weight:700">${text}</strong>` : text);
      }
      return parts.join("");
    }).join("<br>");
  }

  /**
   * 处理 .md 文件
   * - 转为 HTML
   * - 找出所有本地图片引用
   * - 返回 { title, bodyHtml, imagePaths }
   */
  static async processMarkdown(filePath) {
    const content = fs.readFileSync(filePath, "utf-8");
    const baseDir = path.dirname(path.resolve(filePath));
    const imagePaths = [];

    // 先用 markdown-it 渲染 HTML
    let bodyHtml = md.render(content);

    // 微信编辑器导入 HTML 时会把块级标签间的换行/缩进空白渲染成多余空行，
    // 故压缩标签间空白（`</p>\n    <p>` → `</p><p>`）；<pre> 内的空白必须保留。
    bodyHtml = bodyHtml.replace(/<pre[\s\S]*?<\/pre>|>\s+</g, (m) =>
      m.startsWith("<pre") ? m : "><"
    );

    // 对 markdown 生成的 HTML 进行 WeChat 兼容性美化（表格/引用/标题等）
    bodyHtml = styleMarkdownHTML(bodyHtml);

    // 找出所有本地图片引用，上传后替换
    const imgRegex = /<img\s+[^>]*src\s*=\s*"([^"]+)"[^>]*>/gi;
    let match;

    while ((match = imgRegex.exec(bodyHtml)) !== null) {
      const src = match[1];

      // 跳过外部 URL 和 data URI
      if (
        src.startsWith("http://") ||
        src.startsWith("https://") ||
        src.startsWith("data:")
      ) {
        continue;
      }

      // 解析图片路径：相对于 markdown 文件所在目录，或绝对路径
      const resolvedPath = path.isAbsolute(src)
        ? src
        : path.resolve(baseDir, src);

      if (!fs.existsSync(resolvedPath)) {
        console.warn(`  ⚠️  图片文件不存在，跳过: ${resolvedPath}`);
        continue;
      }

      // 将 HTML 中的相对路径替换为绝对路径,使主流程的图片替换/上传逻辑生效
      bodyHtml = bodyHtml.split(`src="${src}"`).join(`src="${resolvedPath}"`);
      imagePaths.push(resolvedPath);
    }

    // 提取 markdown 标题：第一个 # 标题
    const h1Match = content.match(/^#\s+(.+)/m);
    const docTitle = h1Match ? h1Match[1].trim() : "";
    const title = docTitle || DocumentProcessor.extractTitle(filePath);
    return { title, bodyHtml, imagePaths, baseDir };
  }

  static generateDigest(htmlContent) {
    const clean = htmlContent.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
    // 取前 35 字，尽量在句号/问号等自然断点处截断
    if (clean.length <= 35) return clean;
    const slice = clean.substring(0, 35);
    // 在 slice 范围内找句号/问号/感叹号
    const boundary = slice.match(/[。！？.!?，,;；]/);
    if (boundary && boundary.index >= 10) {
      return slice.substring(0, boundary.index + 1).trim();
    }
    return slice.trim();
  }

  static extractTitle(filePath) {
    const basename = path.basename(filePath, path.extname(filePath));
    // 将连字符/下划线替换为空格，首字母大写
    return basename
      .replace(/[-_]/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase())
      .trim();
  }

}

// ─── 图片预处理 ──────────────────────────────────────────────────────
/**
 * 给图片加圆角 + 轻微阴影 + 尺寸上限，提升视觉质感。
 * 输入任意格式图片，输出 PNG（为支持圆角透明）。
 * 如果处理失败（如 GIF），返回原路径。
 */
async function preprocessImage(inputPath, outDir) {
  const ext = path.extname(inputPath).toLowerCase();
  // GIF/SVG 跳过
  if (ext === ".gif" || ext === ".svg") return inputPath;

  try {
    const img = sharp(inputPath);
    const meta = await img.metadata();
    let w = meta.width;
    let h = meta.height;

    // 上限宽度 1080px（适合微信文章排版）
    const MAX_W = 1080;
    if (w > MAX_W) {
      h = Math.round(h * (MAX_W / w));
      w = MAX_W;
    }

    // 圆角 + 阴影参数
    const radius = Math.min(10, Math.min(w, h) * 0.03); // 圆角半径，最大 10
    const pad = Math.max(12, Math.min(20, Math.round(w * 0.02))); // 内边距
    const dx = 2; // 阴影水平偏移
    const dy = 4; // 阴影垂直偏移
    const blur = 6; // 阴影模糊
    const shadowOpacity = 0.10; // 阴影透明度

    const canvasW = w + pad * 2;
    const canvasH = h + pad * 2;

    // 阴影层 SVG
    const shadowSvg = Buffer.from(
      `<svg width="${canvasW}" height="${canvasH}">
        <defs>
          <filter id="b" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="${blur}"/>
          </filter>
        </defs>
        <rect x="${pad + dx}" y="${pad + dy}" width="${w}" height="${h}"
              rx="${radius}" ry="${radius}" fill="rgba(0,0,0,${shadowOpacity})" filter="url(#b)"/>
      </svg>`
    );

    // 圆角遮罩 SVG
    const roundedSvg = Buffer.from(
      `<svg width="${w}" height="${h}">
        <rect x="0" y="0" width="${w}" height="${h}" rx="${radius}" ry="${radius}" fill="white"/>
      </svg>`
    );

    const outPath = path.join(
      outDir,
      path.basename(inputPath).replace(/(\.[^.]+)$/, "_processed.png")
    );

    // 先生成圆角图片
    const roundedImg = await img
      .resize(w, h, { fit: "cover", withoutEnlargement: true })
      .png()
      .composite([{ input: roundedSvg, blend: "dest-in" }])
      .toBuffer();

    // 合成阴影 + 圆角图片
    await sharp(shadowSvg)
      .composite([{ input: roundedImg, top: pad, left: pad }])
      .png()
      .toFile(outPath);

    console.log(`      🎨 已美化 (圆角${radius}px + 阴影)`);
    return outPath;
  } catch (err) {
    console.warn(`      ⚠️  图片预处理失败，使用原图: ${err.message}`);
    return inputPath;
  }
}

// ─── 网络重试 ──────────────────────────────────────────────────────
// 微信接口偶发超时/限流，transient 失败重试 1 次
async function withRetry(fn, retries = 1) {
  let lastErr;
  for (let i = 0; i <= retries; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      if (i < retries) {
        console.warn(`   ⚠️  请求失败，${1}s 后重试 (${i + 1}/${retries}): ${err.message}`);
        await new Promise((r) => setTimeout(r, 1000));
      }
    }
  }
  throw lastErr;
}

// ─── 发布前自检 ──────────────────────────────────────────────────────
// 检查生成的 HTML 是否符合排版规范，不通过则不发布（对齐"交付前自检"铁律）
function selfCheck({ bodyHtml, title, imagePaths }) {
  const checks = [];

  const goldCount = (bodyHtml.match(/border-left:3px solid #C9A227/g) || []).length;
  checks.push({ name: "标题金色左划线", pass: goldCount > 0, detail: `金色标题 ${goldCount} 处` });

  const hasTable = /<table[\s>]/.test(bodyHtml);
  const deepHeader = (bodyHtml.match(/background:#1A3A6B/g) || []).length > 0;
  checks.push({ name: "表格深蓝表头", pass: !hasTable || deepHeader, detail: hasTable ? (deepHeader ? "表头深蓝已渲染" : "有表格但无深蓝表头") : "无表格（跳过）" });

  const hasFooter = /【延伸阅读】|mp-common-profile/.test(bodyHtml);
  checks.push({ name: "签名 footer", pass: hasFooter, detail: hasFooter ? "已拼接" : "缺失 footer" });

  // footer 占位符检测：footer.html 若仍是 {{占位符}} 模板，严禁发布（脚本化，替代 AI 人工检查）
  const footerPlaceholder = (bodyHtml.match(/\{\{[^}]{1,80}\}\}/g) || []).slice(0, 3);
  checks.push({
    name: "footer 无占位符",
    pass: footerPlaceholder.length === 0,
    detail: footerPlaceholder.length ? `footer 仍含占位符: ${footerPlaceholder.join(" | ")}（请先配置 footer.html）` : "无占位符",
  });

  const titleLen = Array.from(title).length;
  checks.push({ name: "标题长度 ≤64", pass: titleLen <= 64, detail: `${titleLen} 字（Unicode 码点）` });

  const missing = imagePaths.filter((p) => !fs.existsSync(p));
  checks.push({ name: "图片文件存在", pass: missing.length === 0, detail: missing.length ? `缺失 ${missing.length} 张` : `全部 ${imagePaths.length} 张` });

  // 正文重点句加粗检测（warning，不阻断发布）：
  // 加粗是「写稿/排版」环节的职责，发布脚本只透传 docx 里已有的 run 级加粗。
  // 若正文一片 15px 无任何加粗（只有标题 17/18px 加粗），多半是漏做了「语义加粗」。
  // 两类特征：docx 正文重点句 = font-size:15px;font-weight:700；markdown 正文 strong = font-weight:700;color:#1a1a1a。
  const docxBoldCount = (bodyHtml.match(/font-size:15px;font-weight:700/g) || []).length;
  const mdBoldCount = (bodyHtml.match(/<strong style="font-weight:700;color:#1a1a1a"/g) || []).length;
  const bodyBoldCount = docxBoldCount + mdBoldCount;
  const bodyBoldWarn = bodyBoldCount === 0
    ? "正文无任何重点句加粗（仅标题加粗）——请确认是否漏做「语义加粗」，需要时回排版环节补"
    : null;

  return { checks, allPass: checks.every((c) => c.pass), warnings: bodyBoldWarn ? [bodyBoldWarn] : [] };
}

function printSelfCheckReport(report) {
  console.log("\n📋 自检报告:");
  for (const c of report.checks) {
    console.log(`   ${c.pass ? "✅" : "❌"} ${c.name}: ${c.detail}`);
  }
  if (report.warnings && report.warnings.length) {
    for (const w of report.warnings) {
      console.log(`   ⚠️ ${w}`);
    }
  }
}

// ─── 主流程 ──────────────────────────────────────────────────────────
async function main() {
  const args = process.argv.slice(2);
  const checkMode = args.includes("--check");
  const filePath = args.find((a) => !a.startsWith("--"));

  if (!filePath) {
    console.error("用法: node publish.js <文件路径.docx|.md> [--check]");
    console.error("示例: node publish.js ./我的文章.docx           # 直接发布");
    console.error("      node publish.js ./我的文章.docx --check   # 仅自检，不调用微信");
    process.exit(1);
  }

  const resolvedPath = path.resolve(filePath);
  if (!fs.existsSync(resolvedPath)) {
    console.error(`文件不存在: ${resolvedPath}`);
    process.exit(1);
  }

  const ext = path.extname(resolvedPath).toLowerCase();
  if (ext !== ".docx" && ext !== ".md") {
    console.error(`不支持的格式: ${ext}（仅支持 .docx 和 .md）`);
    process.exit(1);
  }

  // ── 加载配置 ──
  const config = loadConfig();
  let tempDirs = [];

  try {
    // ── 1. 解析文档（--check 与发布共用）──
    console.log(`\n📄 正在解析文档: ${path.basename(resolvedPath)}`);

    let title, bodyHtml, imagePaths;
    if (ext === ".docx") {
      const result = await DocumentProcessor.processDocx(resolvedPath);
      title = result.title;
      bodyHtml = result.bodyHtml;
      imagePaths = result.imagePaths;
      if (result.tempDir) tempDirs.push(result.tempDir);
    } else {
      const result = await DocumentProcessor.processMarkdown(resolvedPath);
      title = result.title;
      bodyHtml = result.bodyHtml;
      imagePaths = result.imagePaths;
    }

    const titleChars = Array.from(title);
    if (titleChars.length > 64) {
      console.warn(`   ⚠️  标题超 64 字符（按 Unicode 码点计 ${titleChars.length}），已截断前 64 字`);
      title = titleChars.slice(0, 64).join("");
    }
    console.log(`   标题: ${title}`);
    console.log(`   图片数: ${imagePaths.length}`);

    // ── 将占位符替换为实际图片标签 ──
    imagePaths.forEach((imgPath, i) => {
      bodyHtml = bodyHtml.replace(`<!--IMG_PLACEHOLDER_${i}-->`, `<p style="text-align:center;margin:13px 0;line-height:2.0;"><img src="${imgPath}" style="max-width:100%;display:inline-block;" /></p>`);
    });

    // ── 2. 附加签名区块 + section 包裹（不调微信 API）──
    const footerPath = config.footerFile;
    if (fs.existsSync(footerPath)) {
      console.log(`\n📋 附加签名区块: ${path.basename(footerPath)}`);
      bodyHtml += "\n" + fs.readFileSync(footerPath, "utf-8");
    } else {
      console.log(`\nℹ️  未找到签名文件，跳过 (${footerPath})`);
    }
    bodyHtml = `<section style="line-height: 2.0">${bodyHtml}</section>`;

    // ── 3. 发布前自检（在任何微信 API 调用之前！不过不发，零 API 消耗）──
    const report = selfCheck({ bodyHtml, title, imagePaths });
    printSelfCheckReport(report);

    if (checkMode) {
      const diagDir = fs.mkdtempSync(path.join(os.tmpdir(), "wechat-diag-"));
      const diagFile = path.join(diagDir, "wechat-body.html");
      fs.writeFileSync(diagFile, bodyHtml);
      console.log(`\n📄 --check 模式：诊断 HTML 已存 ${diagFile}（未调用微信 API）`);
      process.exitCode = report.allPass ? 0 : 1;
      return;
    }

    if (!report.allPass) {
      console.error(`\n❌ 自检未通过，中止发布（未调用任何微信 API，修复后重试）`);
      process.exitCode = 1;
      return;
    }

    // ── 4. 自检通过后才调微信 API：图片预处理 + 上传微信 CDN ──
    const client = new WeChatClient(config);
    console.log("\n🔑 正在获取微信 access_token...");
    await client.init();

    if (imagePaths.length > 0) {
      const procDir = fs.mkdtempSync(path.join(os.tmpdir(), "wechat-proc-"));
      tempDirs.push(procDir);
      console.log(`\n🖼️  预处理 ${imagePaths.length} 张图片（圆角+阴影+尺寸上限）...`);

      const uploadPaths = [];
      for (let i = 0; i < imagePaths.length; i++) {
        const oldPath = imagePaths[i];
        process.stdout.write(`   [${i + 1}/${imagePaths.length}] ${path.basename(oldPath)}`);

        let imgPath = oldPath;
        if (config.processImages) {
          imgPath = await preprocessImage(oldPath, procDir);
        }

        // 如果预处理创建了新文件，更新 bodyHtml 中的路径
        if (imgPath !== oldPath) {
          const escapedOld = oldPath.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
          bodyHtml = bodyHtml.replace(new RegExp(escapedOld, "g"), imgPath);
        }

        uploadPaths.push(imgPath);
        console.log("");
      }

      console.log(`\n☁️  正在上传 ${uploadPaths.length} 张图片到微信 CDN...`);
      for (let i = 0; i < uploadPaths.length; i++) {
        const imgPath = uploadPaths[i];
        process.stdout.write(`   [${i + 1}/${uploadPaths.length}] ${path.basename(imgPath)}`);

        const cdnUrl = await client.uploadImage(imgPath);
        const escapedPath = imgPath.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        bodyHtml = bodyHtml.replace(new RegExp(escapedPath, "g"), cdnUrl);
        console.log(` → ☁️`);
      }
      console.log(`   ✅ 所有图片已上传到微信 CDN`);
    } else {
      console.log(`\nℹ️  文档中没有本地图片需要上传`);
    }

    // ── 5. 检查 HTML 中是否还有未处理的本地路径 ──
    const remainingLocal = bodyHtml.match(/src\s*=\s*"(?!https?:\/\/|data:)[^"]+"/g);
    if (remainingLocal) {
      console.warn(`\n⚠️  以下 ${remainingLocal.length} 个图片引用未能上传，请在公众号后台手动处理:`);
      remainingLocal.forEach((ref) => console.warn(`   ${ref}`));
    }

    // ── 6. 诊断：保存生成的 HTML 到临时文件 ──
    const diagDir = fs.mkdtempSync(path.join(os.tmpdir(), "wechat-diag-"));
    tempDirs.push(diagDir);
    fs.writeFileSync(path.join(diagDir, "wechat-body.html"), bodyHtml);

    // ── 7. 创建/更新草稿 ──
    console.log(`\n📝 发布到微信公众号草稿箱...`);
    const draftResult = await client.createOrUpdateDraft(title, bodyHtml);

    const actionLabel = draftResult.action === "updated" ? "更新" : "新建";
    console.log(`\n✅ 草稿${actionLabel}成功！`);
    console.log(`   标题: ${title}`);
    console.log(`   草稿 media_id: ${draftResult.media_id}`);
    console.log(`   操作: ${actionLabel === "更新" ? "原地更新了旧草稿" : "首次发布"}`);
    console.log(`   请登录公众号后台 → 草稿箱 → 可查看、编辑并群发`);
    console.log(`   https://mp.weixin.qq.com/cgi-bin/appmsg`);
  } catch (err) {
    console.error(`\n❌ 操作失败: ${err.message}`);
    if (err.response) {
      const detail = err.response.data || err.response.statusText;
      console.error(`   HTTP ${err.response.status}: ${JSON.stringify(detail)}`);
    }
    process.exitCode = 1; // 不 process.exit()，让 finally 清理临时目录
  } finally {
    // 清理临时目录
    for (const dir of tempDirs) {
      if (fs.existsSync(dir)) {
        fs.rmSync(dir, { recursive: true, force: true });
      }
    }
  }
}

main();
