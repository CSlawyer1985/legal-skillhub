#!/usr/bin/env node

const axios = require('axios');
const cheerio = require('cheerio');
const { program } = require('commander');
const fs = require('fs');

// 配置命令行参数
program
  .name('patent-scout')
  .description('中国专利搜索工具 - 支持多数据源真实搜索')
  .version('2.0.0')
  .option('-q, --query <keywords>', '搜索关键词')
  .option('-p, --patent-id <id>', '专利号（如 CN116789012A）')
  .option('-l, --limit <number>', '结果数量', '10')
  .option('-o, --output <file>', '输出文件')
  .option('-f, --format <format>', '输出格式 (markdown|json)', 'markdown')
  .option('-s, --source <source>', '数据源 (google|baidu)', 'baidu')
  .option('--proxy <proxy>', '代理地址（如 http://127.0.0.1:7890）')
  .parse(process.argv);

const options = program.opts();

// HTTP 请求配置
function getHttpConfig() {
  const config = {
    timeout: 20000,
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
  };
  if (options.proxy) {
    const { HttpsProxyAgent } = require('https-proxy-agent');
    config.httpsAgent = new HttpsProxyAgent(options.proxy);
    config.proxy = false;
  }
  return config;
}

const REQUEST_DELAY = 1500;
function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

// ==================== 百度搜索中国专利（国内直连） ====================

async function searchBaiduPatents(query, limit = 10) {
  console.error(`正在通过百度搜索中国专利: ${query}`);
  const results = [];
  const seenIds = new Set(); // 去重

  // 多轮搜索策略：先精准后宽泛
  const searchStrategies = [
    { suffix: ' 专利 CN 公开号', desc: '精准专利搜索' },
    { suffix: ' 专利 发明 申请', desc: '宽泛专利搜索' },
  ];

  for (const strategy of searchStrategies) {
    if (results.length >= limit) break;
    console.error(`策略: ${strategy.desc}`);
    const strategyResults = await _baiduSearch(`${query}${strategy.suffix}`, limit - results.length);
    for (const r of strategyResults) {
      if (results.length >= limit) break;
      // 去重：同一个专利号不重复
      if (r.patent_id.startsWith('RESULT_') || !seenIds.has(r.patent_id)) {
        if (!r.patent_id.startsWith('RESULT_')) seenIds.add(r.patent_id);
        results.push(r);
      }
    }
    if (results.length < limit) await sleep(REQUEST_DELAY);
  }

  return results.slice(0, limit);
}

// 百度搜索内部实现
async function _baiduSearch(searchQuery, limit) {
  const results = [];
  const httpConfig = getHttpConfig();
  httpConfig.headers['Cookie'] = 'BAIDUID=RANDOM' + Date.now() + ':FG=1';
  httpConfig.headers['Referer'] = 'https://www.baidu.com/';

  const pageSize = 10;
  const pages = Math.ceil(limit / pageSize);

  for (let page = 0; page < pages && results.length < limit; page++) {
    try {
      const pn = page * pageSize;
      const url = `https://www.baidu.com/s?wd=${encodeURIComponent(searchQuery)}&pn=${pn}&rn=${pageSize}`;
      console.error(`  请求第 ${page + 1} 页...`);

      const response = await axios.get(url, httpConfig);
      const $ = cheerio.load(response.data);

      $('.result, .c-container').each((i, el) => {
        if (results.length >= limit) return false;
        const $el = $(el);
        const title = $el.find('h3 a, .t a').first().text().trim().replace(/\s+/g, ' ');
        const link = $el.find('h3 a, .t a').first().attr('href') || '';
        const snippet = $el.find('.c-abstract, .content-right_8Zs40, [class*="abstract"], [class*="content"]').first().text().trim().replace(/\s+/g, ' ');

        const fullText = title + ' ' + snippet;
        const patentId = extractPatentId(fullText);

        const isAd = link.includes('baidu.com/baidu.php') || link.includes('e.baidu.com') || title.includes('广告');
        if (title && !isAd && (patentId || fullText.includes('专利') || fullText.includes('发明'))) {
          const meta = extractMetaFromSnippet(fullText);
          results.push({
            patent_id: patentId || `RESULT_${results.length + 1}`,
            title: cleanTitle(title),
            abstract: cleanSnippet(snippet),
            applicants: meta.applicants,
            inventors: meta.inventors,
            application_date: meta.application_date,
            publication_date: meta.publication_date,
            legal_status: meta.legal_status || '未知',
            ipc_classes: [],
            claims: [],
            url: link,
            source: 'baidu'
          });
        }
      });

      if (page < pages - 1) await sleep(REQUEST_DELAY);
    } catch (err) {
      console.error(`  百度搜索第 ${page + 1} 页失败: ${err.message}`);
      break;
    }
  }

  return results;
}

// ==================== Google Patents 搜索（需代理） ====================

async function searchGooglePatents(query, limit = 10) {
  console.error(`正在通过 Google Patents 搜索中国专利: ${query}`);
  const results = [];
  const httpConfig = getHttpConfig();

  try {
    const url = `https://patents.google.com/?q=${encodeURIComponent(query)}&country=CN&oq=${encodeURIComponent(query)}&num=${limit}`;
    console.error(`请求: ${url}`);

    const response = await axios.get(url, httpConfig);
    const $ = cheerio.load(response.data);

    // 解析搜索结果
    $('search-result-item, article, .search-result-item').each((i, el) => {
      if (results.length >= limit) return false;
      const $el = $(el);
      const title = $el.find('h3, .result-title, span#htmlContent').first().text().trim();
      const snippet = $el.find('.abstract, .result-snippet').first().text().trim();
      const link = $el.find('a[href*="patent"]').first().attr('href') || '';
      const patentId = extractPatentId(link) || extractPatentId(title);

      if (title && patentId) {
        results.push({
          patent_id: patentId,
          title: title,
          abstract: snippet || '（查看详情获取摘要）',
          applicants: [],
          inventors: [],
          application_date: '',
          publication_date: '',
          legal_status: '未知',
          ipc_classes: [],
          claims: [],
          url: link.startsWith('http') ? link : `https://patents.google.com${link}`,
          source: 'google_patents'
        });
      }
    });
  } catch (err) {
    console.error(`Google Patents 搜索失败: ${err.message}`);
    if (!options.proxy) {
      console.error('💡 提示: 如果无法访问 Google，请使用 --proxy 参数或切换到百度源 (-s baidu)');
    }
  }

  return results;
}

// 通过 Google Patents 获取专利详情
async function getGooglePatentDetail(patentId) {
  console.error(`正在获取专利详情: ${patentId}`);
  const url = `https://patents.google.com/patent/${patentId}/zh`;
  const httpConfig = getHttpConfig();

  try {
    const response = await axios.get(url, httpConfig);
    const $ = cheerio.load(response.data);

    const title = $('h1#title').text().trim() || $('title').text().replace(/ - Google Patents.*/, '').trim();
    const abstract = $('div.abstract').text().trim();
    const applicants = [];
    $('dd[itemprop="assigneeOriginal"]').each((i, el) => {
      const name = $(el).text().trim();
      if (name) applicants.push(name);
    });
    const inventors = [];
    $('dd[itemprop="inventor"]').each((i, el) => {
      const name = $(el).text().trim();
      if (name) inventors.push(name);
    });
    const applicationDate = $('time[itemprop="filingDate"]').attr('datetime') || '';
    const publicationDate = $('time[itemprop="publicationDate"]').attr('datetime') || '';
    const legalStatus = $('span[itemprop="status"]').first().text().trim();
    const ipcClasses = [];
    $('span[itemprop="Code"]').each((i, el) => {
      const code = $(el).text().trim();
      if (code.match(/^[A-H]\d/)) ipcClasses.push(code);
    });
    const claims = [];
    $('div.claims .claim').each((i, el) => {
      const text = $(el).text().trim();
      if (text.length > 10) claims.push(text);
    });

    return {
      patent_id: patentId, title: title || patentId, abstract: abstract || '（未获取到摘要）',
      applicants, inventors, application_date: applicationDate, publication_date: publicationDate,
      legal_status: legalStatus || '未知', ipc_classes: ipcClasses, claims: claims.slice(0, 10),
      url, source: 'google_patents'
    };
  } catch (err) {
    console.error(`获取详情失败: ${err.message}`);
    return {
      patent_id: patentId, title: patentId, abstract: `获取失败: ${err.message}`,
      applicants: [], inventors: [], application_date: '', publication_date: '',
      legal_status: '未知', ipc_classes: [], claims: [], url, source: 'google_patents'
    };
  }
}

// ==================== 工具函数 ====================

function extractPatentId(text) {
  if (!text) return null;
  // 匹配中国专利号格式，按优先级排列
  const patterns = [
    /CN\d{6,}[A-Z]\d?/gi,           // CN305342340S, CN116789012A, CN121567465A
    /CN\d{12,}\.\d+/gi,             // CN202310052420.3 (申请号带小数点)
    /CN\d{6,}/gi,                    // CN305342340 (纯数字，无后缀字母)
  ];
  for (const pat of patterns) {
    const match = text.match(pat);
    if (match) return match[0].replace(/\s/g, '').toUpperCase();
  }
  // 从 URL 中提取
  const urlMatch = text.match(/patent\/(CN\d+[A-Z]?\d?)/i);
  if (urlMatch) return urlMatch[1].toUpperCase();
  // 匹配"申请公布号"、"公开号"等标签后面的编号
  const labelMatch = text.match(/(?:申请公布号|公开号|申请号|公告号|公开\(公告\)号)[：:\s]*([A-Z]*\d{6,}[A-Z.]?\d*)/i);
  if (labelMatch) {
    let id = labelMatch[1].replace(/\s/g, '').toUpperCase();
    if (/^\d/.test(id)) id = 'CN' + id;
    return id;
  }
  // 匹配"专利申请号为CN..."的模式
  const inlineMatch = text.match(/专利[申请]*号[为是：:\s]*(CN\d{6,}[A-Z.]?\d*)/i);
  if (inlineMatch) return inlineMatch[1].replace(/\s/g, '').toUpperCase();
  return null;
}

function extractDate(text) {
  if (!text) return '';
  const match = text.match(/(\d{4})[年\-\/](\d{1,2})?[月\-\/]?(\d{1,2})?/);
  if (match) {
    const y = match[1];
    const m = match[2] ? match[2].padStart(2, '0') : '01';
    const d = match[3] ? match[3].padStart(2, '0') : '01';
    return `${y}-${m}-${d}`;
  }
  return '';
}

function cleanTitle(title) {
  if (!title) return '';
  let clean = title.replace(/<[^>]+>/g, '');
  // 去掉常见网站名后缀（- 或 _ 分隔）
  const siteNames = [
    '天眼查', '爱企查', '企查查', '道客巴巴', '百度百科', '百度学术',
    '知乎', '搜狐网', '搜狐', '网易', '新浪', '腾讯网', '凤凰网',
    'ZAKER', '金融界', '证券之星', '查大', '豆丁网', '百度文库',
    '专利查询', '专利搜索', '国家知识产权局'
  ];
  for (const site of siteNames) {
    // 直接用 indexOf 查找并截断，避免正则转义问题
    const separators = [' - ', ' _ ', ' | ', '- ', '_ ', '| '];
    for (const sep of separators) {
      const idx = clean.indexOf(sep + site);
      if (idx !== -1) {
        clean = clean.substring(0, idx);
        break;
      }
    }
  }
  return clean.replace(/\s+/g, ' ').trim();
}

// 清洗 snippet 中的噪音文本
function cleanSnippet(snippet) {
  if (!snippet) return '（查看详情获取摘要）';
  let clean = snippet;
  // 去掉常见噪音
  clean = clean.replace(/\s*(播报|暂停|收听|展开|收起|查看更多|点击查看)\s*/g, ' ');
  // 去掉网站名
  clean = clean.replace(/\s*(天眼查|爱企查|企查查|道客巴巴|百度百科|百度学术|搜狐网|搜狐|ZAKER|金融界|证券之星|X技术|豆丁网)\s*/g, ' ');
  // 去掉日期来源标记（如 "2026年2月26日"后面跟的来源）
  clean = clean.replace(/www\.\w+\.com/g, '');
  return clean.replace(/\s+/g, ' ').trim() || '（查看详情获取摘要）';
}

// 从百度 snippet 中提取结构化信息（申请人、发明人、日期等）
function extractMetaFromSnippet(text) {
  const meta = { applicants: [], inventors: [], application_date: '', publication_date: '', legal_status: '' };
  if (!text) return meta;

  // 提取申请人
  const applicantMatch = text.match(/申请人[：:\s]*([^\n,;，；(（]{2,}?)(?=\s*(?:地址|住所|专利|代理|发明|摘要|分类|$))/);
  if (applicantMatch) {
    let raw = applicantMatch[1].trim();
    // 去掉末尾可能粘连的网站名
    raw = raw.replace(/\s*(天眼查|爱企查|企查查|百度|搜狐|知乎|ZAKER|金融界).*$/, '');
    meta.applicants = raw.split(/[、\/]/).map(s => s.trim()).filter(s => s.length > 1 && s.length < 30);
  }

  // 提取发明人
  const inventorMatch = text.match(/发明人[：:\s]*([^\n(（]+?)(?=\s*(?:申请|专利|地址|摘要|住所|代理|分类|\.{3}|$))/);
  if (inventorMatch) {
    const raw = inventorMatch[1].trim();
    meta.inventors = raw.split(/[、;；\s]+/)
      .map(s => s.trim())
      .filter(s => s.length >= 2 && s.length <= 4 && /^[\u4e00-\u9fa5]+$/.test(s));
  }

  // 提取申请日期
  const appDateMatch = text.match(/申请日[期：:\s]*(\d{4}[\-年\.\/]\d{1,2}[\-月\.\/]?\d{0,2})/);
  if (appDateMatch) meta.application_date = extractDate(appDateMatch[1]);

  // 提取公开/公告日期
  const pubDateMatch = text.match(/(?:公开|公告|公布)[日(（]?[期）)：:\s]*(\d{4}[\-年\.\/]\d{1,2}[\-月\.\/]?\d{0,2})/);
  if (pubDateMatch) meta.publication_date = extractDate(pubDateMatch[1]);

  // 提取法律状态
  const statusMatch = text.match(/(?:法律状态|状态)[：:\s]*([\u4e00-\u9fa5]{2,6})/);
  if (statusMatch) {
    const s = statusMatch[1];
    if (['有效', '授权', '已授权', '审查中', '实审', '公开', '失效', '驳回', '撤回'].includes(s)) {
      meta.legal_status = s;
    }
  }
  // 也匹配独立出现的状态关键词
  if (!meta.legal_status) {
    if (/有效|已授权/.test(text)) meta.legal_status = '有效';
    else if (/审查中|实质审查/.test(text)) meta.legal_status = '审查中';
  }

  return meta;
}

// ==================== 输出格式化 ====================

function formatMarkdown(results, query) {
  let md = `# 中国专利搜索结果\n\n`;
  md += `**搜索关键词**: ${query || '无'}\n`;
  md += `**数据源**: ${results[0]?.source === 'google_patents' ? 'Google Patents' : '百度学术'}\n`;
  md += `**结果数量**: ${results.length}\n`;
  md += `**搜索时间**: ${new Date().toLocaleString('zh-CN')}\n\n`;
  md += `---\n\n`;

  results.forEach((patent, index) => {
    md += `## ${index + 1}. ${patent.title}\n\n`;
    md += `**专利号**: ${patent.patent_id}\n`;
    if (patent.applicants?.length > 0) md += `**申请人**: ${patent.applicants.join(', ')}\n`;
    if (patent.inventors?.length > 0) md += `**发明人**: ${patent.inventors.join(', ')}\n`;
    if (patent.application_date) md += `**申请日期**: ${patent.application_date}\n`;
    if (patent.publication_date) md += `**公开日期**: ${patent.publication_date}\n`;
    if (patent.legal_status && patent.legal_status !== '未知') md += `**法律状态**: ${patent.legal_status}\n`;
    if (patent.ipc_classes?.length > 0) md += `**IPC 分类**: ${patent.ipc_classes.join(', ')}\n`;
    md += `\n**摘要**:\n${patent.abstract}\n\n`;
    if (patent.claims?.length > 0) {
      md += `**权利要求**:\n`;
      patent.claims.forEach(claim => { md += `${claim}\n\n`; });
    }
    if (patent.url) md += `**详情链接**: ${patent.url}\n\n`;
    md += `---\n\n`;
  });

  return md;
}

// ==================== 主函数 ====================

async function main() {
  try {
    let results = [];
    const source = options.source || 'baidu';

    // 专利号查询
    if (options.patentId) {
      let pid = options.patentId.toUpperCase().replace(/\s/g, '');
      if (/^\d/.test(pid)) pid = 'CN' + pid;

      if (source === 'google') {
        const detail = await getGooglePatentDetail(pid);
        results = [detail];
      } else {
        // 百度源用关键词搜专利号
        results = await searchBaiduPatents(pid, 1);
        if (results.length === 0) {
          // 回退到构造基本信息
          results = [{
            patent_id: pid,
            title: pid,
            abstract: '请通过 Google Patents 或国家知识产权局网站查看详情',
            applicants: [], inventors: [],
            application_date: '', publication_date: '',
            legal_status: '未知', ipc_classes: [], claims: [],
            url: `https://patents.google.com/patent/${pid}/zh`,
            source: 'baidu_xueshu'
          }];
        }
      }
    }
    // 关键词搜索
    else if (options.query) {
      if (source === 'google') {
        results = await searchGooglePatents(options.query, parseInt(options.limit));
      } else {
        results = await searchBaiduPatents(options.query, parseInt(options.limit));
      }

      if (results.length === 0) {
        console.error(`❌ 未找到关键词"${options.query}"的相关中国专利`);
        if (source === 'google') {
          console.error('💡 提示: 如果无法访问 Google，请使用 -s baidu 切换到百度学术');
        } else {
          console.error('💡 提示: 可尝试换个关键词，或使用 -s google --proxy http://127.0.0.1:7890 切换到 Google Patents');
        }
        process.exit(0);
      }
    } else {
      console.error('❌ 错误: 请提供搜索关键词 (--query) 或专利号 (--patent-id)');
      console.error('\n📖 使用示例:');
      console.error('   node scripts/patent-search.js --query "工业防火墙"');
      console.error('   node scripts/patent-search.js --query "深度学习" -s baidu');
      console.error('   node scripts/patent-search.js --query "5G" -s google --proxy http://127.0.0.1:7890');
      console.error('   node scripts/patent-search.js --patent-id CN116789012A');
      console.error('   node scripts/patent-search.js --query "固态电池" --limit 5 --output results.md');
      process.exit(1);
    }

    console.error(`\n✅ 获取到 ${results.length} 条专利信息\n`);

    // 格式化输出
    let output;
    if (options.format === 'json') {
      output = JSON.stringify(results, null, 2);
    } else {
      output = formatMarkdown(results, options.query || options.patentId);
    }

    // 输出到文件或控制台
    if (options.output) {
      fs.writeFileSync(options.output, output, 'utf8');
      console.error(`💾 结果已保存到: ${options.output}`);
    } else {
      console.log(output);
    }

    process.exit(0);
  } catch (error) {
    console.error('❌ 执行失败:', error.message);
    process.exit(1);
  }
}

main();
