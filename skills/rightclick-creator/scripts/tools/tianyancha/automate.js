const { chromium } = require('playwright');

async function openTianyancha(companyName) {
    // 使用 Chrome 浏览器而不是 Chromium
    const browser = await chromium.launch({
        headless: false,
        channel: 'chrome',  // 使用用户安装的 Chrome
        args: ['--disable-blink-features=AutomationControlled']
    });

    const context = await browser.newContext();
    const page = await context.newPage();

    // 打开天眼查搜索页面
    const searchUrl = companyName
        ? `https://www.tianyancha.com/search?key=${encodeURIComponent(companyName)}`
        : 'https://www.tianyancha.com/';

    await page.goto(searchUrl, { waitUntil: 'networkidle' });

    console.log('已打开天眼查');
}

module.exports = {
    openTianyancha
};
