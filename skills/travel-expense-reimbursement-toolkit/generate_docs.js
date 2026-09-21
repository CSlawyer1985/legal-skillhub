const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, BorderStyle, WidthType, ShadingType, PageBreak,
  Footer, PageNumber
} = require("docx");

const DATA_PATH = "./expense_data.json";
const IMAGE_DIRS = ["./images", "./"];
const SIZES_PATH = "./image_sizes.json";
const OUT_DIR = "./";

// 读取图片尺寸缓存，如果文件不存在则用空对象（会回退到从文件头直接读取）
let SIZES = {};
try {
  SIZES = JSON.parse(fs.readFileSync(SIZES_PATH, "utf-8"));
} catch (e) {
  // image_sizes.json 不存在，后续会从图片文件头直接读取尺寸，不影响结果
}

function findImagePath(caseShort, imgName) {
  if (!imgName || imgName === "__no_image__") return null;
  for (const dir of IMAGE_DIRS) {
    const p = path.join(dir, caseShort, imgName);
    if (fs.existsSync(p)) return p;
  }
  return null;
}

// A4 portrait: 11906 x 16838 DXA, 1-inch margins => content ~9026 DXA wide ~ 15.8cm
// Available height ~ 14038 DXA ~ 24.6cm
// Image max: width 15cm, height 18cm (leave room for text above)
const MAX_IMG_W_PX = 500;
const MAX_IMG_H_PX = 650;

// 直接从图片文件头读取实际尺寸（不依赖image_sizes.json）
// 避免basename匹配导致跨案件尺寸混淆
function getActualImageSize(imgPath) {
  const buf = fs.readFileSync(imgPath);
  let width = 0, height = 0;

  if (buf.length < 24) return null;

  // PNG: 签名 89 50 4E 47, IHDR在偏移16
  if (buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4E && buf[3] === 0x47) {
    width = buf.readUInt32BE(16);
    height = buf.readUInt32BE(20);
    return { width, height, ratio: height / width };
  }

  // JPEG: 扫描SOF0/SOF1/SOF2标记 (0xFFC0/0xFFC1/0xFFC2)
  if (buf[0] === 0xFF && buf[1] === 0xD8) {
    let offset = 2;
    while (offset < buf.length - 9) {
      if (buf[offset] !== 0xFF) { offset++; continue; }
      const marker = buf[offset + 1];
      // SOF markers: C0, C1, C2, C3, C5, C6, C7, C9, CA, CB, CD, CE, CF
      if (marker >= 0xC0 && marker <= 0xCF && marker !== 0xC4 && marker !== 0xC8 && marker !== 0xCC) {
        height = buf.readUInt16BE(offset + 5);
        width = buf.readUInt16BE(offset + 7);
        return { width, height, ratio: height / width };
      }
      // 跳过这个marker的段
      if (offset + 3 < buf.length) {
        const segLen = buf.readUInt16BE(offset + 2);
        offset += 2 + segLen;
      } else {
        break;
      }
    }
  }

  // BMP: 偏移18是宽度，22是高度（小端uint32）
  if (buf[0] === 0x42 && buf[1] === 0x4D) {
    width = buf.readUInt32LE(18);
    height = buf.readUInt32LE(22);
    return { width, height, ratio: height / width };
  }

  // GIF: 偏移6是宽度，8是高度（小端uint16）
  if (buf[0] === 0x47 && buf[1] === 0x49 && buf[2] === 0x46) {
    width = buf.readUInt16LE(6);
    height = buf.readUInt16LE(8);
    return { width, height, ratio: height / width };
  }

  return null;
}

function getImageInfo(imgPath) {
  // 优先：直接从文件头读取实际尺寸（最准确）
  const actual = getActualImageSize(imgPath);
  if (actual) return actual;

  // 回退：从image_sizes.json查找
  let info = SIZES[imgPath];
  if (!info) {
    const fwdPath = imgPath.replace(/\\/g, "/");
    info = SIZES[fwdPath];
  }
  if (!info) {
    const backPath = imgPath.replace(/\//g, "\\");
    info = SIZES[backPath];
  }
  if (!info) {
    console.warn(`  WARNING: Cannot read image size for ${imgPath}, using default`);
    return { width: 1080, height: 400, ratio: 0.37 };
  }
  return info;
}

function calcImageSizePx(imgPath) {
  const info = getImageInfo(imgPath);
  const ratio = info.ratio; // height/width
  // Start with max width, calculate height
  let dispW = MAX_IMG_W_PX;
  let dispH = Math.round(MAX_IMG_W_PX * ratio);
  // If height exceeds max, scale down by height
  if (dispH > MAX_IMG_H_PX) {
    dispH = MAX_IMG_H_PX;
    dispW = Math.round(MAX_IMG_H_PX / ratio);
  }
  return { w: dispW, h: dispH };
}

function getImageType(filename) {
  const ext = path.extname(filename).toLowerCase();
  if (ext === ".png") return "png";
  if (ext === ".jpg" || ext === ".jpeg") return "jpg";
  if (ext === ".bmp") return "bmp";
  if (ext === ".gif") return "gif";
  return "png";
}

function createCell(text, width, options = {}) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: "999999" };
  const runOpts = { text: String(text), size: 18, font: "微软雅黑" };
  if (options.color) runOpts.color = options.color;
  if (options.bold) runOpts.bold = true;
  return new TableCell({
    borders: { top: border, bottom: border, left: border, right: border },
    width: { size: width, type: WidthType.DXA },
    shading: options.shading ? { fill: "F0F0F0", type: ShadingType.CLEAR } : (options.fill ? { fill: options.fill, type: ShadingType.CLEAR } : undefined),
    verticalAlign: "center",
    margins: { top: 60, bottom: 60, left: 80, right: 80 },
    children: [new Paragraph({
      alignment: options.align || AlignmentType.LEFT,
      children: [new TextRun(runOpts)]
    })]
  });
}

function createHeaderCell(text, width) {
  return createCell(text, width, { shading: true, align: AlignmentType.CENTER });
}

async function generateDocx(caseData) {
  const caseName = caseData.case_name;
  const total = caseData.total;
  const items = caseData.items;
  const alerts = caseData.alerts || [];

  const commonBorder = { style: BorderStyle.SINGLE, size: 1, color: "999999" };
  const totalBorder = { top: commonBorder, bottom: commonBorder, left: commonBorder, right: commonBorder };

  // Build table rows
  const headerRow = new TableRow({
    children: [
      createHeaderCell("序号", 500),
      createHeaderCell("日期", 1100),
      createHeaderCell("时间", 700),
      createHeaderCell("事项/摘要", 1800),
      createHeaderCell("起点", 1200),
      createHeaderCell("终点", 1200),
      createHeaderCell("金额(元)", 1000),
      createHeaderCell("备注", 1860),
    ]
  });

  const itemRows = items.map(item => {
    // Date cell: red if from dialog, red+(推测) if inferred
    let dateText = item.date;
    let dateOpts = {};
    if (item.date_source === "dialog") {
      dateOpts = { color: "CC0000", fill: "FFF3E0" };
    } else if (item.date_source === "inferred") {
      dateText = `${item.date}（推测）`;
      dateOpts = { color: "CC0000", fill: "FFF3E0" };
    }
    return new TableRow({
      children: [
        createCell(item.seq, 500, { align: AlignmentType.CENTER }),
        createCell(dateText, 1100, dateOpts),
        createCell(item.time || "—", 700),
        createCell(item.type, 1800),
        createCell(item.from, 1200),
        createCell(item.to, 1200),
        createCell(item.amount.toFixed(2), 1000, { align: AlignmentType.RIGHT }),
        createCell(item.note, 1860),
      ]
    });
  });

  const totalRow = new TableRow({
    children: [
      new TableCell({
        borders: totalBorder,
        width: { size: 500, type: WidthType.DXA },
        shading: { fill: "FFF8E1", type: ShadingType.CLEAR },
        columnSpan: 6,
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "合计", bold: true, size: 18, font: "微软雅黑" })]
        })]
      }),
      new TableCell({
        borders: totalBorder,
        width: { size: 1000, type: WidthType.DXA },
        shading: { fill: "FFF8E1", type: ShadingType.CLEAR },
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: total.toFixed(2), bold: true, size: 18, font: "微软雅黑" })]
        })]
      }),
      new TableCell({
        borders: totalBorder,
        width: { size: 1860, type: WidthType.DXA },
        shading: { fill: "FFF8E1", type: ShadingType.CLEAR },
        children: [new Paragraph({ children: [] })]
      }),
    ]
  });

  const table = new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [500, 1100, 700, 1800, 1200, 1200, 1000, 1860],
    rows: [headerRow, ...itemRows, totalRow]
  });

  // Build image attachment section
  // Collect unique images and their associated items
  const imgMap = new Map();
  items.forEach(item => {
    const imgPath = findImagePath(caseData.case_short, item.img);
    if (!imgPath) {
      if (item.img && item.img !== "__no_image__") {
        console.warn(`  WARNING: Image not found: ${item.img} in case ${caseData.case_short}`);
      }
      return;
    }
    if (!imgMap.has(imgPath)) {
      imgMap.set(imgPath, { items: [], seqNumbers: [] });
    }
    const entry = imgMap.get(imgPath);
    entry.items.push(item);
    if (!entry.seqNumbers.includes(item.seq)) {
      entry.seqNumbers.push(item.seq);
    }
  });

  const imgEntries = Array.from(imgMap.entries());

  // 按截图分组打印，供操作者复核日期（防止同图多日期误套首日期）
  console.log("\n=== 按截图分组复核（请确认每条日期与截图日期表头一致）===");
  imgEntries.forEach(([imgPath, meta]) => {
    const dates = [...new Set(meta.items.map(it => it.date))];
    const multiDate = dates.length > 1 ? `  ⚠ 含${dates.length}个日期: ${dates.join(", ")}` : "";
    console.log(`  ${path.basename(imgPath)}: 序号${meta.seqNumbers.join(",")}${multiDate}`);
  });
  console.log("");

  const attachmentChildren = [];

  imgEntries.forEach(([imgPath, meta], idx) => {
    const sizePx = calcImageSizePx(imgPath);
    const imgType = getImageType(imgPath);
    const imgData = fs.readFileSync(imgPath);

    // PageBreak before each image (except the first)
    if (idx > 0) {
      attachmentChildren.push(new Paragraph({ children: [new PageBreak()] }));
    }

    // --- Text section (top) ---

    // Caption title
    attachmentChildren.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 100, after: 80 },
      children: [
        new TextRun({ text: `凭证图${meta.seqNumbers.join(",")}`, bold: true, size: 22, font: "微软雅黑" })
      ]
    }));

    // Table info for each order
    meta.items.forEach(item => {
      const dateStr = item.time ? `${item.date} ${item.time}` : item.date;
      const line = `序号${item.seq} ｜ ${dateStr} ｜ ${item.type} ｜ ${item.from} → ${item.to} ｜ ¥${item.amount.toFixed(2)}`;
      attachmentChildren.push(new Paragraph({
        alignment: AlignmentType.LEFT,
        spacing: { before: 30, after: 30 },
        children: [new TextRun({ text: line, size: 18, font: "微软雅黑" })]
      }));
      if (item.note) {
        attachmentChildren.push(new Paragraph({
          alignment: AlignmentType.LEFT,
          spacing: { before: 20, after: 20 },
          children: [new TextRun({ text: `备注：${item.note}`, size: 16, font: "微软雅黑", color: "666666" })]
        }));
      }
    });

    // Empty line (spacer)
    attachmentChildren.push(new Paragraph({ children: [] }));

    // --- Image section (bottom, inline, no wrapping) ---
    attachmentChildren.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new ImageRun({
        type: imgType,
        data: imgData,
        transformation: { width: sizePx.w, height: sizePx.h },
        altText: { title: `图${meta.seqNumbers.join(",")}`, description: `${meta.items[0].date} ${meta.items[0].type}凭证`, name: `img${idx}` }
      })]
    }));
  });

  // Alert section
  const alertChildren = [];
  if (alerts.length > 0) {
    alertChildren.push(new Paragraph({ children: [new PageBreak()] }));
    alertChildren.push(new Paragraph({
      spacing: { before: 200, after: 200 },
      children: [new TextRun({ text: "⚠ 异常提醒", bold: true, size: 28, color: "CC0000", font: "微软雅黑" })]
    }));
    for (const alert of alerts) {
      alertChildren.push(new Paragraph({
        children: [new TextRun({ text: "• " + alert, size: 20, color: "CC0000", font: "微软雅黑" })]
      }));
    }
  }

  // Build prepayment attachment (always show, even if no prepayment)
  const prepaymentChildren = [];
  prepaymentChildren.push(new Paragraph({
    spacing: { before: 200, after: 200 },
    children: [new TextRun({ text: "二、预支费用凭证", bold: true, size: 28, font: "微软雅黑" })]
  }));

  if (caseData.prepayment) {
    const prep = caseData.prepayment;
    const prepPath = findImagePath(caseData.case_short, prep.img);
    if (prepPath && fs.existsSync(prepPath)) {
      const prepImgType = getImageType(prepPath);
      const prepImgData = fs.readFileSync(prepPath);
      const prepSizePx = calcImageSizePx(prepPath);

      prepaymentChildren.push(new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 100, after: 80 },
        children: [new TextRun({ text: "预支凭证", bold: true, size: 22, font: "微软雅黑" })]
      }));
      prepaymentChildren.push(new Paragraph({
        alignment: AlignmentType.LEFT,
        spacing: { before: 30, after: 30 },
        children: [new TextRun({ text: `当事人于 ${prep.date} 预支差旅费 ${prep.amount.toFixed(2)} 元`, size: 18, font: "微软雅黑" })]
      }));
      prepaymentChildren.push(new Paragraph({ children: [] }));
      prepaymentChildren.push(new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new ImageRun({
          type: prepImgType,
          data: prepImgData,
          transformation: { width: prepSizePx.w, height: prepSizePx.h },
          altText: { title: "预支凭证", description: "当事人预支差旅费转账截图", name: "prepayment" }
        })]
      }));
    }
  } else {
    // 无预支费用，明确写明"无"
    prepaymentChildren.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 200 },
      children: [new TextRun({ text: "本案件当事人未预支差旅费，无预支凭证。", size: 22, font: "微软雅黑", color: "666666" })]
    }));
  }

  // Create footer with page numbers
  const docFooter = new Footer({
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "第 ", size: 18, font: "微软雅黑" }),
          new TextRun({ children: [PageNumber.CURRENT], size: 18, font: "微软雅黑" }),
          new TextRun({ text: " 页 共 ", size: 18, font: "微软雅黑" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, font: "微软雅黑" }),
          new TextRun({ text: " 页", size: 18, font: "微软雅黑" })
        ]
      })
    ]
  });

  // Build prepayment summary section at the top (all cases show this)
  const summaryChildren = [];
  if (caseData.prepayment) {
    const prep = caseData.prepayment;
    const diff = total - prep.amount;
    summaryChildren.push(new Paragraph({
      spacing: { before: 100, after: 100 },
      children: [
        new TextRun({ text: "【费用结算说明】", bold: true, size: 22, font: "微软雅黑", color: "333333" })
      ]
    }));
    summaryChildren.push(new Paragraph({
      spacing: { after: 60 },
      children: [
        new TextRun({ text: "一、当事人已预支差旅费用：", size: 20, font: "微软雅黑" }),
        new TextRun({ text: `${prep.amount.toFixed(2)} 元`, bold: true, size: 20, font: "微软雅黑", color: "CC0000" }),
        new TextRun({ text: `（于 ${prep.date} 支付，凭证见附件）`, size: 18, font: "微软雅黑", color: "666666" })
      ]
    }));
    summaryChildren.push(new Paragraph({
      spacing: { after: 60 },
      children: [
        new TextRun({ text: "二、本案件实际发生差旅费用：", size: 20, font: "微软雅黑" }),
        new TextRun({ text: `${total.toFixed(2)} 元`, bold: true, size: 20, font: "微软雅黑", color: "CC0000" })
      ]
    }));
    if (diff > 0) {
      // 实际 > 预支，当事人需补交
      summaryChildren.push(new Paragraph({
        spacing: { after: 60 },
        children: [
          new TextRun({ text: "三、经核算，当事人尚需补交：", size: 20, font: "微软雅黑" }),
          new TextRun({ text: `${diff.toFixed(2)} 元`, bold: true, size: 20, font: "微软雅黑", color: "CC0000" })
        ]
      }));
      summaryChildren.push(new Paragraph({
        spacing: { after: 200 },
        children: [
          new TextRun({ text: "四、待向当事人退还：", size: 20, font: "微软雅黑", color: "999999" }),
          new TextRun({ text: "0.00 元", size: 20, font: "微软雅黑", color: "999999" })
        ]
      }));
    } else if (diff < 0) {
      // 预支 > 实际，需退还当事人
      const refund = Math.abs(diff);
      summaryChildren.push(new Paragraph({
        spacing: { after: 60 },
        children: [
          new TextRun({ text: "三、经核算，当事人尚需补交：", size: 20, font: "微软雅黑", color: "999999" }),
          new TextRun({ text: "0.00 元", size: 20, font: "微软雅黑", color: "999999" })
        ]
      }));
      summaryChildren.push(new Paragraph({
        spacing: { after: 200 },
        children: [
          new TextRun({ text: "四、待向当事人退还：", size: 20, font: "微软雅黑" }),
          new TextRun({ text: `${refund.toFixed(2)} 元`, bold: true, size: 20, font: "微软雅黑", color: "CC0000" })
        ]
      }));
    } else {
      // 刚好相等
      summaryChildren.push(new Paragraph({
        spacing: { after: 60 },
        children: [
          new TextRun({ text: "三、经核算，当事人尚需补交：", size: 20, font: "微软雅黑", color: "999999" }),
          new TextRun({ text: "0.00 元", size: 20, font: "微软雅黑", color: "999999" })
        ]
      }));
      summaryChildren.push(new Paragraph({
        spacing: { after: 200 },
        children: [
          new TextRun({ text: "四、待向当事人退还：", size: 20, font: "微软雅黑", color: "999999" }),
          new TextRun({ text: "0.00 元", size: 20, font: "微软雅黑", color: "999999" })
        ]
      }));
    }
  } else {
    // 无预支费用的情况
    summaryChildren.push(new Paragraph({
      spacing: { before: 100, after: 100 },
      children: [
        new TextRun({ text: "【费用结算说明】", bold: true, size: 22, font: "微软雅黑", color: "333333" })
      ]
    }));
    summaryChildren.push(new Paragraph({
      spacing: { after: 60 },
      children: [
        new TextRun({ text: "一、当事人已预支差旅费用：", size: 20, font: "微软雅黑" }),
        new TextRun({ text: "0.00 元", bold: true, size: 20, font: "微软雅黑", color: "999999" }),
        new TextRun({ text: "（本案件当事人未预支差旅费）", size: 18, font: "微软雅黑", color: "666666" })
      ]
    }));
    summaryChildren.push(new Paragraph({
      spacing: { after: 60 },
      children: [
        new TextRun({ text: "二、本案件实际发生差旅费用：", size: 20, font: "微软雅黑" }),
        new TextRun({ text: `${total.toFixed(2)} 元`, bold: true, size: 20, font: "微软雅黑", color: "CC0000" })
      ]
    }));
    summaryChildren.push(new Paragraph({
      spacing: { after: 60 },
      children: [
        new TextRun({ text: "三、经核算，当事人尚需补交：", size: 20, font: "微软雅黑" }),
        new TextRun({ text: `${total.toFixed(2)} 元`, bold: true, size: 20, font: "微软雅黑", color: "CC0000" })
      ]
    }));
    summaryChildren.push(new Paragraph({
      spacing: { after: 200 },
      children: [
        new TextRun({ text: "四、待向当事人退还：", size: 20, font: "微软雅黑", color: "999999" }),
        new TextRun({ text: "0.00 元", size: 20, font: "微软雅黑", color: "999999" })
      ]
    }));
  }

  const doc = new Document({
    styles: {
      default: {
        document: {
          run: { font: "微软雅黑", size: 22 }
        }
      }
    },
    sections: [{
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
        }
      },
      footers: { default: docFooter },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          children: [new TextRun({ text: "差旅费报销单", bold: true, size: 36, font: "微软雅黑" })]
        }),
        ...summaryChildren,
        new Paragraph({
          spacing: { after: 100 },
          children: [
            new TextRun({ text: "案件名称：", bold: true, size: 22, font: "微软雅黑" }),
            new TextRun({ text: caseName, size: 22, font: "微软雅黑" })
          ]
        }),
        new Paragraph({
          spacing: { after: 200 },
          children: (() => {
            const runs = [];
            if (caseData.prepayment) {
              const diff = total - caseData.prepayment.amount;
              runs.push(new TextRun({ text: "当事人已预支：", bold: true, size: 22, font: "微软雅黑" }));
              runs.push(new TextRun({ text: caseData.prepayment.amount.toFixed(2) + " 元", size: 22, font: "微软雅黑" }));
              runs.push(new TextRun({ text: "    实际发生报销：", bold: true, size: 22, font: "微软雅黑" }));
              runs.push(new TextRun({ text: total.toFixed(2) + " 元", size: 22, font: "微软雅黑" }));
              runs.push(new TextRun({ text: `（共${items.length}条）`, size: 20, font: "微软雅黑", color: "666666" }));
              if (diff > 0) {
                runs.push(new TextRun({ text: "    当事人尚需补交：", bold: true, size: 22, font: "微软雅黑" }));
                runs.push(new TextRun({ text: diff.toFixed(2) + " 元", bold: true, size: 22, font: "微软雅黑", color: "CC0000" }));
              } else if (diff < 0) {
                runs.push(new TextRun({ text: "    待向当事人退还：", bold: true, size: 22, font: "微软雅黑" }));
                runs.push(new TextRun({ text: Math.abs(diff).toFixed(2) + " 元", bold: true, size: 22, font: "微软雅黑", color: "CC0000" }));
              } else {
                runs.push(new TextRun({ text: "    费用两清", bold: true, size: 22, font: "微软雅黑", color: "999999" }));
              }
            } else {
              runs.push(new TextRun({ text: "当事人未预支", bold: true, size: 22, font: "微软雅黑" }));
              runs.push(new TextRun({ text: "    实际发生报销：", bold: true, size: 22, font: "微软雅黑" }));
              runs.push(new TextRun({ text: total.toFixed(2) + " 元", size: 22, font: "微软雅黑" }));
              runs.push(new TextRun({ text: `（共${items.length}条）`, size: 20, font: "微软雅黑", color: "666666" }));
              runs.push(new TextRun({ text: "    当事人尚需补交：", bold: true, size: 22, font: "微软雅黑" }));
              runs.push(new TextRun({ text: total.toFixed(2) + " 元", bold: true, size: 22, font: "微软雅黑", color: "CC0000" }));
            }
            return runs;
          })()
        }),
        new Paragraph({
          spacing: { before: 200, after: 200 },
          children: [new TextRun({ text: "一、差旅费报销明细表", bold: true, size: 28, font: "微软雅黑" })]
        }),
        table,
        new Paragraph({ children: [new PageBreak()] }),
        ...prepaymentChildren,
        new Paragraph({ children: [new PageBreak()] }),
        new Paragraph({
          spacing: { before: 200, after: 200 },
          children: [new TextRun({ text: "三、差旅费原始凭证附件", bold: true, size: 28, font: "微软雅黑" })]
        }),
        ...attachmentChildren,
        ...alertChildren
      ]
    }]
  });

  const buffer = await Packer.toBuffer(doc);
  // 文件名包含核心数据：预支/实际/补交或退还
  let filename;
  if (caseData.prepayment) {
    const diff = total - caseData.prepayment.amount;
    if (diff > 0) {
      filename = `${caseName}报销单_预支${caseData.prepayment.amount.toFixed(2)}_实际${total.toFixed(2)}_补交${diff.toFixed(2)}.docx`;
    } else if (diff < 0) {
      filename = `${caseName}报销单_预支${caseData.prepayment.amount.toFixed(2)}_实际${total.toFixed(2)}_退还${Math.abs(diff).toFixed(2)}.docx`;
    } else {
      filename = `${caseName}报销单_预支${caseData.prepayment.amount.toFixed(2)}_实际${total.toFixed(2)}_两清.docx`;
    }
  } else {
    filename = `${caseName}报销单_未预支_实际${total.toFixed(2)}_补交${total.toFixed(2)}.docx`;
  }
  const outPath = path.join(OUT_DIR, filename);
  fs.writeFileSync(outPath, buffer);
  console.log(`Generated: ${outPath} (${imgEntries.length} images)`);
}

async function main() {
  const data = JSON.parse(fs.readFileSync(DATA_PATH, "utf-8"));
  // 自动校正每个案件的total和item_count，避免手动算错
  for (const caseData of data) {
    const actualTotal = Math.round(caseData.items.reduce((s, it) => s + it.amount, 0) * 100) / 100;
    const actualCount = caseData.items.length;
    if (caseData.total !== actualTotal || caseData.item_count !== actualCount) {
      console.warn(`[校正] ${caseData.case_name}: total ${caseData.total} -> ${actualTotal}, count ${caseData.item_count} -> ${actualCount}`);
      caseData.total = actualTotal;
      caseData.item_count = actualCount;
    }
  }
  // 将校正后的数据写回json文件
  fs.writeFileSync(DATA_PATH, JSON.stringify(data, null, 2), "utf-8");
  for (const caseData of data) {
    await generateDocx(caseData);
  }
  console.log("\nAll documents generated successfully!");
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
