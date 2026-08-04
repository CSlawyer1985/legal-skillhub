#!/usr/bin/env node
/**
 * 把含内联 SVG 和 Markdown 表格的专利 Markdown 转成 .docx：
 *   - 文本按行 → docx 段落（已知标题行加粗/居中）
 *   - 每个 <svg>…</svg> → 在原位置渲染成高清 PNG 居中内嵌
 *   - Markdown 表格 → docx 原生表格（带边框、表头加粗、居中）
 *
 * 用法: node svg-to-docx.js <输入.md> [输出.docx]
 */
const fs = require("fs");
const path = require("path");
const { Resvg } = require("@resvg/resvg-js");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, VerticalAlign,
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

/**
 * 解析 Markdown 表格块为数组: [[cell, ...], ...]
 * 自动跳过分隔行 (|:---|...|)
 */
function parseMdTable(lines) {
  return lines
    .filter((l) => !/^\|\s*[:\-]+\s*\|/.test(l.trim()))
    .map((l) =>
      l.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim())
    );
}

/**
 * 将解析后的二维数组转为 docx Table
 */
function mdTableToDocx(rows) {
  if (rows.length === 0) return null;
  const colCount = rows[0].length;
  const colWidthPct = Math.floor(9000 / colCount); // 总宽度 9000 twips

  const borderStyle = {
    style: BorderStyle.SINGLE,
    size: 1,
    color: "000000",
  };
  const borders = {
    top: borderStyle, bottom: borderStyle,
    left: borderStyle, right: borderStyle,
    insideHorizontal: borderStyle, insideVertical: borderStyle,
  };

  const tableRows = rows.map((row, rowIdx) => {
    const isHeader = rowIdx === 0;
    const cells = [];
    for (let i = 0; i < colCount; i++) {
      const text = (row[i] || "").trim();
      cells.push(
        new TableCell({
          width: { size: colWidthPct, type: WidthType.DXA },
          verticalAlign: VerticalAlign.CENTER,
          borders,
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              spacing: { before: 40, after: 40 },
              children: [
                new TextRun({
                  text,
                  bold: isHeader,
                  size: isHeader ? 22 : 20,
                  font: "宋体",
                }),
              ],
            }),
          ],
        })
      );
    }
    return new TableRow({ children: cells });
  });

  return new Table({
    width: { size: 9000, type: WidthType.DXA },
    rows: tableRows,
    alignment: AlignmentType.CENTER,
  });
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

  // ---- 第1步：提取所有 SVG 和表格块的位置 ----
  const svgRe = /<svg[\s\S]*?<\/svg>/g;
  const tblRe = /(^\|.*\|$)(\r?\n(\|\s*[:\-]+\s*\|.*$))?(\r?\n(\|.*\|$))*/gm;

  // 收集所有块: { type, index, length, data }
  const blocks = [];
  let m;
  while ((m = svgRe.exec(md)) !== null) {
    blocks.push({ type: "svg", index: m.index, length: m[0].length, data: m[0] });
  }
  while ((m = tblRe.exec(md)) !== null) {
    // 确认至少有2行（表头+分隔+数据）
    const lines = m[0].split(/\r?\n/).filter((l) => l.trim());
    if (lines.length >= 2) {
      blocks.push({ type: "table", index: m.index, length: m[0].length, data: m[0] });
    }
  }
  // 按位置排序
  blocks.sort((a, b) => a.index - b.index);

  const children = [];
  let figCount = 0;
  let tblCount = 0;
  let skipCount = 0;
  let last = 0;

  const pushText = (chunk) => {
    chunk.split(/\r?\n/).forEach((line) => children.push(textLineToParagraph(line)));
  };

  for (const block of blocks) {
    // 块之前的文本
    if (block.index > last) pushText(md.slice(last, block.index));

    if (block.type === "svg") {
      try {
        const { png, width, height } = renderSvgToPng(block.data);
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
        pushText(block.data);
      }
    } else if (block.type === "table") {
      const lines = block.data.split(/\r?\n/).filter((l) => l.trim());
      const rows = parseMdTable(lines);
      const table = mdTableToDocx(rows);
      if (table) {
        children.push(new Paragraph({ text: "", spacing: { before: 120, after: 40 } }));
        children.push(table);
        children.push(new Paragraph({ text: "", spacing: { before: 40, after: 120 } }));
        tblCount += 1;
      } else {
        pushText(block.data);
      }
    }

    last = block.index + block.length;
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
    return { figCount, tblCount, skipCount };
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
  const { figCount, tblCount, skipCount } = await build(input, output);
  const parts = [];
  if (figCount > 0) parts.push(`${figCount} 张图已高清内嵌`);
  if (tblCount > 0) parts.push(`${tblCount} 个表格已转为原生表格`);
  if (skipCount > 0) parts.push(`${skipCount} 张图渲染失败已跳过`);
  console.error(`[完成] ${parts.join("，")} → ${output}`);
}

main().catch((e) => {
  console.error("[错误] 转换失败:", e.message);
  process.exit(1);
});
