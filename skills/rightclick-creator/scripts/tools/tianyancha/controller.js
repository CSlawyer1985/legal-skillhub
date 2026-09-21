#!/usr/bin/env node

const automate = require('./automate');

async function main() {
    const companyName = process.argv[2] || '';

    console.log('正在打开天眼查...');

    await automate.openTianyancha(companyName);
}

main();
