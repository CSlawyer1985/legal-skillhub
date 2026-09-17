// 通用产业模型渲染器：渲染三层流程 + 数据流图（使用 Skill 内改造版渲染器，不依赖原库）
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { renderProcessMapSvg, renderDataFlowMapSvg } from './generic_v4_renderer.mjs';

export async function renderGeneric(modelPath, outputDir) {
  const model = JSON.parse(await readFile(modelPath, 'utf8'));
  await mkdir(outputDir, { recursive: true });
  const processSvg = renderProcessMapSvg(model);
  const dataflowSvg = renderDataFlowMapSvg(model);
  await writeFile(resolve(outputDir, 'process-map.svg'), processSvg, 'utf8');
  await writeFile(resolve(outputDir, 'data-flow-map.svg'), dataflowSvg, 'utf8');
  return { outputDir, svgViews: ['process-map', 'data-flow-map'] };
}

if (process.argv[1] && import.meta.url === new URL(`file://${resolve(process.argv[1])}`).href) {
  const [modelPath, outputDir] = process.argv.slice(2);
  renderGeneric(resolve(modelPath), resolve(outputDir))
    .then((result) => { console.log(JSON.stringify(result)); })
    .catch((error) => { console.error(error); process.exit(1); });
}
