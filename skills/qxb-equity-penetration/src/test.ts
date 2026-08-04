import { createClient } from './client'

async function main() {
  const client = createClient()

  try {
    const result = await client.getEquityPenetration('深圳市腾讯计算机系统有限公司')
    console.log('=== 企业股权穿透 ===')
    console.log('企业名称:', result.ename)
    console.log('')

    console.log('--- 直接股东 ---')
    console.log('总数:', result.directShareholders.total)
    for (const s of result.directShareholders.items) {
      console.log(`  ${s.name} - ${s.stockPercent}`)
    }
    console.log('')

    console.log('--- 间接股东 ---')
    console.log('总数:', result.indirectShareholders.total)
    for (const s of result.indirectShareholders.items.slice(0, 10)) {
      console.log(`  ${s.name} - ${s.stockPercent} (${s.shortestLevel}层)`)
      if (s.shortestPath.length > 0) {
        const pathStr = s.shortestPath.map(p => `${p.name}(${p.percent})`).join(' -> ')
        console.log(`    路径: ${pathStr}`)
      }
    }
  } catch (error: any) {
    console.error('查询失败:', error.message)
  }
}

main()
