#!/usr/bin/env node

/**
 * 企查查 - 企业信息查询 Skill
 * 
 * 功能：根据公司名称查询企业基本信息、知识产权等
 * 数据来源：天眼查、企查查、爱企查等公开信息
 */

import https from 'https';

// Tavily API 配置（用于搜索企业信息）
const TAVILY_API_KEY = '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';

/**
 * 调用 Tavily 搜索
 */
async function tavilySearch(query) {
  return new Promise((resolve) => {
    const data = JSON.stringify({
      api_key: TAVILY_API_KEY,
      query: query,
      max_results: 8
    });

    const options = {
      hostname: 'api.tavily.com',
      port: 443,
      path: '/search',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      }
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          resolve({ results: [], error: e.message });
        }
      });
    });

    req.on('error', (e) => resolve({ results: [], error: e.message }));
    req.write(data);
    req.end();
  });
}

/**
 * 提取企业基本信息
 */
function extractBasicInfo(results, companyName) {
  const info = {
    name: companyName,
    creditCode: '',
    legalPerson: '',
   注册资本: '',
    实缴资本: '',
    成立日期: '',
    经营状态: '存续',
    企业类型: '有限责任公司',
    注册地址: '',
    经营范围: '',
    联系电话: ''
  };

  for (const r of results) {
    const text = r.content || '';
    
    // 提取统一社会信用代码
    if (text.includes('信用代码') || text.includes('信用代码')) {
      const match = text.match(/信用代码[：:]\s*([A-Z0-9]{18})/);
      if (match) info.creditCode = match[1];
    }
    
    // 提取法定代表人
    if (text.includes('法定代表人') || text.includes('法人代表')) {
      const match = text.match(/(?:法定代表人|法人代表)[：:]\s*([\u4e00-\u9fa5]{2,4})/);
      if (match) info.legalPerson = match[1];
    }
    
    // 提取注册资本
    if (text.includes('注册资本')) {
      const match = text.match(/注册资本[：:]\s*([\d.]+万?元?)/);
      if (match) info.注册资本 = match[1];
    }
    
    // 提取成立日期
    if (text.includes('成立日期') || text.includes('成立时间')) {
      const match = text.match(/(?:成立日期|成立时间)[：:]\s*(\d{4}-\d{2}-\d{2})/);
      if (match) info.成立日期 = match[1];
    }
    
    // 提取经营范围
    if (text.includes('经营范围')) {
      const match = text.match(/经营范围[：:]\s*([^。]+。?)/);
      if (match && match[1].length > 10) info.经营范围 = match[1];
    }
    
    // 提取联系电话
    if (text.includes('电话') || text.includes('联系方式')) {
      const match = text.match(/(?:电话|联系方式)[：:]\s*(\d{3,4}-?\d{7,8})/);
      if (match) info.联系电话 = match[1];
    }
  }

  return info;
}

/**
 * 搜索知识产权信息
 */
async function searchIPInfo(companyName) {
  const ipInfo = {
    patents: [],
    trademarks: [],
    copyrights: []
  };

  // 搜索专利
  const patentResults = await tavilySearch(`${companyName} 专利 发明专利 实用新型 外观设计`);
  for (const r of patentResults.results || []) {
    const text = r.content;
    // 提取专利名称
    const matches = text.matchAll(/专利[：:]\s*([^\n，,；;]{5,50})/g);
    for (const m of matches) {
      if (ipInfo.patents.length < 5) {
        ipInfo.patents.push(m[1].trim());
      }
    }
  }

  // 搜索商标
  const trademarkResults = await tavilySearch(`${companyName} 商标 注册商标 品牌`);
  for (const r of trademarkResults.results || []) {
    const text = r.content;
    const matches = text.matchAll(/商标[：:]\s*([^\n，,；;]{2,20})/g);
    for (const m of matches) {
      if (ipInfo.trademarks.length < 5) {
        ipInfo.trademarks.push(m[1].trim());
      }
    }
  }

  // 搜索著作权
  const copyrightResults = await tavilySearch(`${companyName} 软件著作权 作品著作权`);
  for (const r of copyrightResults.results || []) {
    const text = r.content;
    const matches = text.matchAll(/(?:软件著作权|著作权)[：:]\s*([^\n，,；;]{5,50})/g);
    for (const m of matches) {
      if (ipInfo.copyrights.length < 5) {
        ipInfo.copyrights.push(m[1].trim());
      }
    }
  }

  return ipInfo;
}

/**
 * 格式化输出
 */
function formatOutput(basicInfo, ipInfo) {
  let output = `
╔══════════════════════════════════════════════════════════════╗
║                    企查查 - 企业信息查询                        ║
╠══════════════════════════════════════════════════════════════╣

【基本信息】
┌─────────────────────────────────────────────────────────────┐
│ 企业名称：${basicInfo.name.padEnd(43)}│
│ 统一社会信用代码：${basicInfo.creditCode.padEnd(36)}│
│ 法定代表人：${basicInfo.legalPerson.padEnd(43)}│
│ 企业类型：${basicInfo.企业类型.padEnd(45)}│
│ 经营状态：${basicInfo.经营状态.padEnd(45)}│
├─────────────────────────────────────────────────────────────┤
│ 注册资本：${basicInfo.注册资本.padEnd(45)}│
│ 实缴资本：${basicInfo.实缴资本.padEnd(45)}│
│ 成立日期：${basicInfo.成立日期.padEnd(45)}│
│ 注册地址：${basicInfo.注册地址.padEnd(45)}│
│ 联系电话：${basicInfo.联系电话.padEnd(45)}│
└─────────────────────────────────────────────────────────────┘

【经营范围】
${basicInfo.经营范围 || '详见企查查官网'}

╠══════════════════════════════════════════════════════════════╣
║                     知识产权                                    ║
╠══════════════════════════════════════════════════════════════╣
`;

  // 专利信息
  output += `\n【专利信息】`;
  if (ipInfo.patents.length > 0) {
    ipInfo.patents.forEach((p, i) => {
      output += `\n  ${i + 1}. ${p}`;
    });
  } else {
    output += `\n  暂无公开专利信息`;
  }

  // 商标信息
  output += `\n\n【商标信息】`;
  if (ipInfo.trademarks.length > 0) {
    ipInfo.trademarks.forEach((t, i) => {
      output += `\n  ${i + 1}. ${t}`;
    });
  } else {
    output += `\n  暂无公开商标信息`;
  }

  // 著作权信息
  output += `\n\n【著作权信息】`;
  if (ipInfo.copyrights.length > 0) {
    ipInfo.copyrights.forEach((c, i) => {
      output += `\n  ${i + 1}. ${c}`;
    });
  } else {
    output += `\n  暂无公开著作权信息`;
  }

  output += `

╠══════════════════════════════════════════════════════════════╣
║                     数据来源                                    ║
╠══════════════════════════════════════════════════════════════╣

  🔗 企查查：https://www.qcc.com/web/search?key=${encodeURIComponent(basicInfo.name)}
  🔗 天眼查：https://www.tianyancha.com/search?key=${encodeURIComponent(basicInfo.name)}
  🔗 爱企查：https://www.aiqicha.com/search?word=${encodeURIComponent(basicInfo.name)}

╚══════════════════════════════════════════════════════════════╝
`;
  return output;
}

/**
 * 主函数
 */
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log(`
使用方法: ./qichacha.js "公司名称"

示例:
  ./qichacha.js "腾讯"
  ./qichacha.js "阿里巴巴"
  ./qichacha.js "深圳市图灵机器人有限公司"

输出内容:
  - 基本信息（法人、注册资本、成立日期等）
  - 经营范围
  - 专利信息
  - 商标信息
  - 著作权信息
  - 数据来源链接
`);
    process.exit(0);
  }

  const companyName = args.join(' ');

  console.log(`\n🔍 正在查询: ${companyName}`);
  console.log(`📡 正在获取企业基本信息...`);

  // 1. 搜索基本信息
  const basicResults = await tavilySearch(`${companyName} 工商信息 注册资本 法人 经营范围`);
  const basicInfo = extractBasicInfo(basicResults.results || [], companyName);

  console.log(`📡 正在获取知识产权信息...`);

  // 2. 搜索知识产权
  const ipInfo = await searchIPInfo(companyName);

  // 3. 格式化输出
  const output = formatOutput(basicInfo, ipInfo);
  console.log(output);
}

main().catch(console.error);
