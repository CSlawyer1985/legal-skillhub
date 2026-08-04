# 附录：辅助脚本源码

> 以下为 `svg-to-docx.js` 和 `package.json` 的完整源码副本，供参考或恢复使用。
> 可执行文件本身在 `$DIR/` 根目录下，不需要手动写出。

## package.json

```json
{
  "name": "patent-svg-to-docx",
  "version": "1.1.0",
  "private": true,
  "description": "把含内联 SVG 的专利 md 转成图片原位内嵌的 .docx",
  "type": "commonjs",
  "engines": { "node": ">=18" },
  "dependencies": {
    "@resvg/resvg-js": "^2.6.2",
    "docx": "^9.0.0"
  }
}
```

## svg-to-docx.js

```js
#!/usr/bin/env node
/**
 * 把含内联 SVG 的专利 Markdown 转成 .docx：
 *   - 文本按行 → docx 段落
 *   - 每个 <svg>…</svg> → 在原位置渲染成高清 PNG 居中内嵌
 *
 * 用法: node svg-to-docx.js <输入.md> [输出.docx]
 */
const fs = require("fs");
const path = require("path");
const { Resvg } = require("@resvg/resvg-js");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, AlignmentType,
} = require("docx");

const SVG_ZOOM = 3;
const DISP_MAX_W = 450;
const DISP_MAX_H = 620;

const TOP_HEADINGS = new Set(["权利要求书", "说明书", "说明书摘要", "说明书附图"]);
const SUB_HEADINGS = new Set(["技术领域", "背景技术", "发明内容", "附图说明", "具体实施方式"]);

function stripCodeFences(md) {
  return md.replace(/```svg\r?\n/g, "").replace(/\r?\n```/g, "");
}

function renderSvgToPng(svg) {
  const r = new Resvg(svg, {
    fitTo: { mode: "zoom", value: SVG_ZOOM },
    background: "white",
  }).render();
  return { png: r.asPng(), width: r.width, height: r.height };
}

function displaySize(w, h) {
  const ratio = h / w;
  let dispW = Math.min(w, DISP_MAX_W);
  let dispH = Math.round(dispW * ratio);
  if (dispH > DISP_MAX_H) {
    dispH = DISP_MAX_H;
    dispW = Math.round(dispH / ratio);
  }
  return { width: dispW, height: dispH };
}

function textLineToParagraph(line) {
  const t = line.trim();
  if (t === "") return new Paragraph({ text: "" });
  if (TOP_HEADINGS.has(t)) {
    return new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 240, after: 120 },
      children: [new TextRun({ text: t, bold: true, size: 32 })],
    });
  }
  if (SUB_HEADINGS.has(t)) {
    return new Paragraph({
      spacing: { before: 160, after: 80 },
      children: [new TextRun({ text: t, bold: true, size: 26 })],
    });
  }
  if (/^图\s*\d+$/.test(t)) {
    return new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 40 },
      children: [new TextRun({ text: t, bold: true })],
    });
  }
  return new Paragraph({
    spacing: { after: 60 },
    children: [new TextRun({ text: line })],
  });
}

function build(mdPath, outPath) {
  const rawMd = fs.readFileSync(mdPath, "utf8");
  const md = stripCodeFences(rawMd);
  const svgRe = /<svg[\s\S]*?<\/svg>/g;
  const children = [];
  let figCount = 0;
  let skipCount = 0;
  let last = 0;
  let m;

  const pushText = (chunk) => {
    chunk.split(/\r?\n/).forEach((line) => children.push(textLineToParagraph(line)));
  };

  while ((m = svgRe.exec(md)) !== null) {
    if (m.index > last) pushText(md.slice(last, m.index));
    try {
      const { png, width, height } = renderSvgToPng(m[0]);
      const disp = displaySize(width, height);
      children.push(new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 40, after: 160 },
        children: [new ImageRun({ type: "png", data: png, transformation: disp })],
      }));
      figCount += 1;
    } catch (e) {
      console.error("[警告] SVG 渲染失败，跳过: " + e.message);
      skipCount++;
      pushText(m[0]);
    }
    last = svgRe.lastIndex;
  }
  if (last < md.length) pushText(md.slice(last));

  if (skipCount > 0) {
    console.error(`[提示] ${skipCount} 张图渲染失败已跳过`);
  }

  const doc = new Document({
    styles: { default: { document: { run: { font: "宋体", size: 24 } } } },
    sections: [{ children }],
  });

  return Packer.toBuffer(doc).then((buf) => {
    fs.writeFileSync(outPath, buf);
    return { figCount, skipCount };
  });
}

async function main() {
  const input = process.argv[2];
  if (!input) {
    console.error("用法: node svg-to-docx.js <输入.md> [输出.docx]");
    process.exit(1);
  }
  const output = process.argv[3]
    || path.join(path.dirname(input), path.basename(input, path.extname(input)) + ".docx");
  const { figCount, skipCount } = await build(input, output);
  if (skipCount > 0) {
    console.error(`[完成] ${figCount} 张图已高清内嵌，${skipCount} 张渲染失败已跳过 → ${output}`);
  } else {
    console.error(`[完成] ${figCount} 张图已高清内嵌 → ${output}`);
  }
}

main().catch((e) => {
  console.error("[错误] 转换失败:", e.message);
  process.exit(1);
});
```
