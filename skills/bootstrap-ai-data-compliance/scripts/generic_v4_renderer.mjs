import { routeOrthogonalEdge } from './orthogonal_router.mjs';

const esc = (value) => String(value ?? '')
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;');

const attr = (values) => esc((values ?? []).join(' '));

function lines(value, max = 12, limit = 3) {
  const source = String(value ?? '');
  const result = [];
  for (let index = 0; index < source.length && result.length < limit; index += max) result.push(source.slice(index, index + max));
  if (source.length > max * limit) result[limit - 1] = `${result[limit - 1].slice(0, -1)}…`;
  return result;
}

function textLines(value, x, y, options = {}) {
  const fontSize = options.fontSize ?? 13;
  const lineHeight = options.lineHeight ?? Math.round(fontSize * 1.35);
  return `<text x="${x}" y="${y}" text-anchor="${options.anchor ?? 'middle'}" class="${options.className ?? ''}" font-size="${fontSize}">${lines(value, options.max ?? 12, options.limit ?? 3).map((line, index) => `<tspan x="${x}" dy="${index === 0 ? 0 : lineHeight}">${esc(line)}</tspan>`).join('')}</text>`;
}

function processStyles() {
  return `<style>
    .title{font:700 28px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#173851}.subtitle{font:13px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#64798c}
    .stage-title{font:700 12px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#173851}.stage-id{font:700 11px ui-monospace,monospace;fill:#6b7f90}.row-label{font:700 14px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#fff}.node-title{font-weight:700;fill:#173851}.node-meta{fill:#657b8e}.process-node{cursor:pointer}.process-node rect{stroke-width:1.5}.process-node:hover rect,.process-node.is-related rect{stroke:#0e7490;stroke-width:4;filter:drop-shadow(0 4px 5px rgba(14,116,144,.22))}.process-node.is-dimmed{opacity:.18}.layer-link{fill:none;stroke:#9bb0bf;stroke-width:1.5;stroke-dasharray:4 5}.badge{font:700 10px ui-monospace,monospace}.legal-note{font:700 12px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#a23b36}.process-help{font:12px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#326985}
  </style>`;
}

export function renderProcessMapSvg(model) {
  const map = model.processMap;
  const left = 170;
  const columnWidth = 190;
  const nodeWidth = 166;
  const headerY = 86;
  const headerHeight = 82;
  const rowHeight = 102;
  // 通用模型：路径来自模型 phases（默认单路径 P1 回退到 A 行）；脑机接口版保留 A/B/C
  const pathIds = [...new Set((map.businessNodes || []).flatMap((node) => node.paths || []).filter(Boolean))];
  const usedPaths = pathIds.length ? pathIds : ['A'];
  const knownYs = { A: 190, B: 292, C: 394, TECHNOLOGY: 516, DATA: 638 };
  const rowYs = { ...knownYs };
  usedPaths.forEach((pathId, index) => { if (!(pathId in knownYs)) rowYs[pathId] = 190 + index * 102; });
  const width = left + map.stages.length * columnWidth + 34;
  const height = 812;
  const pathColors = { A: '#e8f1f8', B: '#eaf4ea', C: '#fff2df' };
  const pathColorFor = (pathId) => pathColors[pathId] ?? '#e8f1f8';
  const rowYFor = (pathId) => rowYs[pathId] ?? rowYs.A;

  const stageHeaders = map.stages.map((stage, index) => {
    const x = left + index * columnWidth;
    return `<g class="process-stage" data-stage-id="${stage.id}"><rect x="${x + 6}" y="${headerY}" width="${nodeWidth}" height="${headerHeight}" rx="12" fill="${index % 2 ? '#f3f6f8' : '#edf3f6'}" stroke="#c8d4dc"/><text x="${x + 18}" y="${headerY + 23}" class="stage-id">${stage.id}｜${stage.index}</text>${textLines(stage.name, x + columnWidth / 2 - 2, headerY + 45, { className: 'stage-title', max: 10, limit: 2, fontSize: 12, lineHeight: 17 })}</g>`;
  }).join('');

  const layerLinks = map.layerLinks.map((link) => {
    const stageIndex = Number(link.to.slice(-2)) - 1;
    const pathId = link.from.split('-')[1];
    const fromY = rowYFor(pathId) + 82;
    const toY = link.to.startsWith('TN') ? rowYs.TECHNOLOGY : rowYs.DATA;
    const x = left + stageIndex * columnWidth + columnWidth / 2 - 2;
    return `<path class="layer-link" data-link-id="${link.id}" data-from="${link.from}" data-to="${link.to}" d="M ${x} ${fromY} L ${x} ${toY}"/>`;
  }).join('');

  const businessNodes = map.businessNodes.map((node) => {
    const stageIndex = Number(node.stageId.slice(1)) - 1;
    const pathId = (node.paths || ['A'])[0];
    const x = left + stageIndex * columnWidth + 6;
    const y = rowYFor(pathId);
    const strokeColor = pathId === 'A' ? '#6f9cba' : pathId === 'B' ? '#78a278' : pathId === 'C' ? '#c69553' : '#6f9cba';
    return `<g class="process-node business-node diagram-node" tabindex="0" data-node-id="${node.id}" data-layer="BUSINESS" data-paths="${attr(node.paths)}" data-stage-id="${node.stageId}" data-event-ids="${attr(node.eventIds)}" data-risk-ids="${attr(node.riskIds)}" data-gate-ids="${attr(node.gateIds)}" data-document-ids="${attr(node.documentIds)}"><title>${esc(pathId)}｜${esc(node.title)}｜待核实</title><rect x="${x}" y="${y}" width="${nodeWidth}" height="82" rx="11" fill="${pathColorFor(pathId)}" stroke="${strokeColor}"/>${textLines(node.title, x + nodeWidth / 2, y + 28, { className: 'node-title', max: 10, limit: 2, fontSize: 13, lineHeight: 17 })}<text x="${x + 10}" y="${y + 70}" class="node-meta" font-size="10">责任主体｜待核实</text><text x="${x + nodeWidth - 10}" y="${y + 70}" text-anchor="end" class="badge" fill="#b9453f">R${node.riskIds.length} G${node.gateIds.length} D${node.documentIds.length}</text></g>`;
  }).join('');

  const sharedNode = (node, y, className, fill, stroke) => {
    const stageIndex = Number(node.stageId.slice(1)) - 1;
    const x = left + stageIndex * columnWidth + 6;
    return `<g class="process-node ${className} diagram-node" tabindex="0" data-node-id="${node.id}" data-layer="${node.layer}" data-paths="${attr(node.paths)}" data-stage-id="${node.stageId}" data-event-ids="${attr(node.eventIds)}" data-risk-ids="${attr(node.riskIds)}" data-gate-ids="${attr(node.gateIds)}" data-document-ids="${attr(node.documentIds)}"><title>${esc(node.title)}｜待核实</title><rect x="${x}" y="${y}" width="${nodeWidth}" height="96" rx="11" fill="${fill}" stroke="${stroke}"/>${textLines(node.title, x + nodeWidth / 2, y + 28, { className: 'node-title', max: 10, limit: 3, fontSize: 12, lineHeight: 16 })}<text x="${x + 10}" y="${y + 84}" class="node-meta" font-size="10">状态｜待核实</text><text x="${x + nodeWidth - 10}" y="${y + 84}" text-anchor="end" class="badge" fill="#b9453f">R${node.riskIds.length} G${node.gateIds.length}</text></g>`;
  };
  const technologyNodes = map.technologyNodes.map((node) => sharedNode(node, rowYs.TECHNOLOGY, 'technology-node', '#eeeaf8', '#8068aa')).join('');
  const dataNodes = map.dataNodes.map((node) => sharedNode(node, rowYs.DATA, 'data-node', '#e5f3ef', '#4c988c')).join('');

  const rowLabel = (id, label, y, color, sub) => `<g><rect x="18" y="${y}" width="132" height="96" rx="12" fill="${color}"/><text x="84" y="${y + 32}" text-anchor="middle" class="row-label">${esc(label)}</text><text x="84" y="${y + 54}" text-anchor="middle" font-size="11" fill="#eaf1f5">${esc(sub)}</text></g>`;
  // 通用模型只显示实际使用的路径行 + 技术/数据层
  const phaseNames = Object.fromEntries((model.phases || []).map((p) => [p.id, p.name]));
  const pathLabels = usedPaths.map((pathId, index) => {
    const y = rowYFor(pathId);
    const label = phaseNames[pathId] || `路径${index + 1}`;
    const sub = pathId === 'A' ? 'A路径' : pathId === 'B' ? 'B路径' : pathId === 'C' ? 'C路径' : `${pathId}路径`;
    const color = pathId === 'A' ? '#326985' : pathId === 'B' ? '#517c46' : pathId === 'C' ? '#9a6b2d' : '#326985';
    return rowLabel(pathId, label, y, color, sub);
  }).join('');
  const phaseCount = usedPaths.length;
  const panelHeight = 86 + phaseCount * 102 + 16;
  const techY = 190 + phaseCount * 102;
  const dataY = techY + 116;
  const industry = model.meta.industry || 'AI产业';
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" data-view="PROCESS" role="img" aria-labelledby="process-title process-desc">${processStyles()}<title id="process-title">${industry}业务—技术—数据三层流程</title><desc id="process-desc">横向${map.stages.length}阶段、纵向业务层、技术层和数据层；全部实际主体和系统待核实。</desc><rect width="100%" height="100%" fill="#f7f9fa"/><text x="22" y="40" class="title">${industry}业务—技术—数据三层流程</text><text x="22" y="66" class="subtitle">横向${map.stages.length}阶段对齐；点击业务节点联动技术与数据节点，风险、闸门和文档在抽屉展开。</text>${stageHeaders}<rect x="8" y="180" width="${width - 16}" height="${panelHeight}" rx="16" fill="#fff" stroke="#d4dee5"/><rect x="8" y="${techY}" width="${width - 16}" height="116" rx="16" fill="#f6f3fb" stroke="#d9d1e8"/><rect x="8" y="${dataY}" width="${width - 16}" height="116" rx="16" fill="#f1f8f6" stroke="#cde2db"/>${pathLabels}${rowLabel('TECH', '技术层', techY, '#6b5795', '共性支撑')}${rowLabel('DATA', '数据层', dataY, '#3d8278', '共性支撑')}${layerLinks}${businessNodes}${technologyNodes}${dataNodes}<text x="22" y="774" class="process-help">点击节点后可查看风险、闸门、文档与待核实事项。</text><text x="${width - 22}" y="774" text-anchor="end" class="legal-note">${esc(model.meta.legalBoundary)}</text></svg>`;
}

function flowStyles() {
  return `<style>
    .title{font:700 28px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#173851}.subtitle{font:13px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#64798c}.system-node{cursor:pointer}.system-node rect{stroke-width:1.7}.system-node:hover rect{stroke:#0e7490;stroke-width:4;filter:drop-shadow(0 4px 5px rgba(14,116,144,.22))}.system-role{font-weight:700;fill:#173851}.system-actual{fill:#b9453f}.data-flow-edge{cursor:pointer}.data-flow-edge .flow-line{fill:none;stroke:#47738e;stroke-width:2.4;marker-end:url(#flow-arrow)}.data-flow-edge:hover .flow-line{stroke:#b9453f;stroke-width:4}.data-flow-edge.is-dimmed,.system-node.is-dimmed{opacity:.12}.closure-edge .flow-line{stroke-dasharray:8 7;stroke-width:2;opacity:.55}.closure-edge .edge-label-bg{fill:#f8fafb;stroke-dasharray:4 3}.edge-hit{fill:none;stroke:transparent;stroke-width:18}.edge-label-bg{fill:#fff;stroke:#aebdc7}.edge-label{font:700 11px ui-monospace,monospace;fill:#173851}.legend-title{font:700 17px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#173851}.legend-item{font:12px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#324f63}.legal-note{font:700 12px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#a23b36}.badge{font:700 9px ui-monospace,monospace;fill:#fff}.institution-zone{fill:#f4f8f4;stroke:#91aa91;stroke-width:1.5;stroke-dasharray:7 6}.institution-zone-title{font:700 12px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;fill:#4d694f}
  </style>`;
}

function boxesOverlap(left, right, padding = 0) {
  return left.x < right.x + right.width + padding
    && left.x + left.width + padding > right.x
    && left.y < right.y + right.height + padding
    && left.y + left.height + padding > right.y;
}

function placeEdgeLabel(route, labelWidth, nodeRects, placedBoxes) {
  const height = 23;
  const candidates = [];
  const segments = route.points.slice(1).map((end, index) => ({ start: route.points[index], end }));
  const sortedSegments = [...segments].sort((left, right) => {
    const leftLength = Math.abs(left.end.x - left.start.x) + Math.abs(left.end.y - left.start.y);
    const rightLength = Math.abs(right.end.x - right.start.x) + Math.abs(right.end.y - right.start.y);
    return rightLength - leftLength;
  });
  for (const segment of sortedSegments) {
    const horizontal = segment.start.y === segment.end.y;
    for (const ratio of [.5, .33, .67]) {
      const midX = segment.start.x + (segment.end.x - segment.start.x) * ratio;
      const midY = segment.start.y + (segment.end.y - segment.start.y) * ratio;
      if (horizontal) {
        for (const offset of [-11, 36, -52, -70, 70]) candidates.push({ labelX: midX, labelY: midY + offset });
      } else {
        candidates.push({ labelX: midX + labelWidth / 2 + 14, labelY: midY });
        candidates.push({ labelX: midX - labelWidth / 2 - 14, labelY: midY });
      }
    }
  }
  candidates.push({ labelX: route.labelX, labelY: route.labelY });
  for (const y of [112, 302, 492, 682, 902]) {
    for (let x = 72 + labelWidth / 2; x <= 1580 - labelWidth / 2; x += 154) candidates.push({ labelX: x, labelY: y });
  }

  for (const candidate of candidates) {
    const box = {
      x: Math.round((candidate.labelX - labelWidth / 2) * 10) / 10,
      y: Math.round((candidate.labelY - 13) * 10) / 10,
      width: labelWidth,
      height
    };
    const insidePanel = box.x >= 25 && box.x + box.width <= 1621 && box.y >= 84 && box.y + box.height <= 924;
    if (!insidePanel) continue;
    if (nodeRects.some((node) => boxesOverlap(box, node, 4))) continue;
    if (placedBoxes.some((placed) => boxesOverlap(box, placed, 4))) continue;
    placedBoxes.push(box);
    return { labelX: box.x + box.width / 2, labelY: box.y + 13, box };
  }
  throw new Error('Unable to place data-flow label without collision');
}

export function renderDataFlowMapSvg(model) {
  const map = model.dataFlowMap;
  const systemNodes = map.systemNodes;
  const width = 2120;
  const height = 1010;
  const nodeWidth = 205;
  const nodeHeight = 104;
  const nodeById = new Map(systemNodes.map((node) => [node.id, node]));
  const nodeRects = systemNodes.map((node) => ({ x: node.x, y: node.y, width: nodeWidth, height: nodeHeight }));
  const placedLabelBoxes = [];
  const colors = { external: ['#fff4e7', '#b78645'], device: ['#eaf2f8', '#5f8fbd'], internal: ['#e9f3ef', '#4c988c'], 'external-tool': ['#f2eefa', '#8068aa'] };
  const edges = map.dataEdges.map((edge, index) => {
    const route = routeOrthogonalEdge({ edge, index, nodes: nodeById, nodeWidth, nodeHeight });
    const label = edge.dataObjectIds.join('·');
    const labelWidth = Math.max(54, label.length * 7 + 18);
    const placement = placeEdgeLabel(route, labelWidth, nodeRects, placedLabelBoxes);
    const dataPoints = route.points.map((point) => `${point.x},${point.y}`).join(' ');
    const labelBox = `${placement.box.x},${placement.box.y},${placement.box.width},${placement.box.height}`;
    const closureEdge = edge.visualRole === 'closure-evidence';
    return `<g class="data-flow-edge${closureEdge ? ' closure-edge' : ''}" tabindex="0" data-edge-id="${edge.id}"${closureEdge ? ' data-closure-edge="true"' : ''} data-route-kind="orthogonal" data-points="${dataPoints}" data-label-box="${labelBox}" data-paths="${attr(edge.paths)}" data-sensitive="${edge.sensitive}" data-external-share="${edge.externalShare}" data-external-tool="${edge.externalTool}" data-event-ids="${attr(edge.eventIds)}" data-risk-ids="${attr(edge.riskIds)}" data-gate-ids="${attr(edge.gateIds)}" data-document-ids="${attr(edge.documentIds)}"><title>${edge.id}｜${esc(label)}｜${esc(edge.provider)}→${esc(edge.recipient)}</title><path class="edge-hit" d="${route.d}"/><path class="flow-line" d="${route.d}" marker-end="url(#flow-arrow)"/><rect class="edge-label-bg" x="${placement.box.x}" y="${placement.box.y}" width="${labelWidth}" height="23" rx="8"/><text class="edge-label" x="${placement.labelX}" y="${placement.labelY + 3}" text-anchor="middle">${label}</text><circle cx="${placement.labelX + labelWidth / 2 - 5}" cy="${placement.labelY - 10}" r="9" fill="#b9453f"/><text class="badge" x="${placement.labelX + labelWidth / 2 - 5}" y="${placement.labelY - 7}" text-anchor="middle">R</text></g>`;
  }).join('');
  const nodes = systemNodes.map((node) => {
    const [fill, stroke] = colors[node.category] ?? colors.internal;
    return `<g class="system-node diagram-node" tabindex="0" data-system-id="${node.id}" data-category="${node.category}"><title>${node.id}｜${esc(node.role)}｜系统名称待核实</title><rect x="${node.x}" y="${node.y}" width="${nodeWidth}" height="${nodeHeight}" rx="13" fill="${fill}" stroke="${stroke}"/>${textLines(node.role, node.x + nodeWidth / 2, node.y + 30, { className: 'system-role', max: 11, limit: 2, fontSize: 13, lineHeight: 18 })}<text x="${node.x + nodeWidth / 2}" y="${node.y + 88}" text-anchor="middle" class="system-actual" font-size="11">【系统名称｜待核实】</text></g>`;
  }).join('');
  const legend = map.dataObjects.map((object, index) => {
    const y = 122 + index * 55;
    return `<g><rect x="1665" y="${y - 22}" width="414" height="44" rx="9" fill="${object.sensitive ? '#fff1ef' : '#f2f6f8'}" stroke="${object.sensitive ? '#e1aaa5' : '#d2dce3'}"/><text x="1680" y="${y + 4}" class="edge-label">${object.id}</text><text x="1730" y="${y + 4}" class="legend-item">${esc(object.name)}</text>${object.sensitive ? `<text x="2062" y="${y + 4}" text-anchor="end" font-size="10" fill="#b9453f">敏感提示</text>` : ''}</g>`;
  }).join('');
  const showInstitution = map.institutionZone !== false;
  const institutionZone = showInstitution ? '<g data-institution-zone="true"><rect class="institution-zone" x="255" y="292" width="465" height="160" rx="16"/><text class="institution-zone-title" x="270" y="318">机构侧外部输入与治理记录｜实际主体及系统待核实</text></g>' : '';
  const industry = model.meta.industry || 'AI产业';
  const dataObjectIds = map.dataObjects.map((o) => o.id);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" data-view="DATAFLOW" role="img" aria-labelledby="flow-title flow-desc">${flowStyles()}<defs><marker id="flow-arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#47738e"/></marker></defs><title id="flow-title">${industry}数据流向图</title><desc id="flow-desc">系统方框和带${dataObjectIds.join('—')}编号的方向箭头；风险和文档仅以徽标提示。</desc><rect width="100%" height="100%" fill="#f7f9fa"/><text x="22" y="40" class="title">${industry}数据流向图</text><text x="22" y="66" class="subtitle">箭头表示数据真实流向，不以时间顺序替代；点击箭头查看字段、用途、接收方、存储、留存与删除去向。</text><rect x="18" y="88" width="1610" height="840" rx="18" fill="#fff" stroke="#d3dee5"/><rect x="1645" y="88" width="454" height="840" rx="18" fill="#eef4f7" stroke="#c8d5dd"/><text x="1665" y="118" class="legend-title">${dataObjectIds.join('—')} 数据对象图例</text>${institutionZone}${edges}${nodes}${legend}<text x="22" y="970" class="subtitle">所有实际系统名称均待核实。</text><text x="${width - 22}" y="970" text-anchor="end" class="legal-note">${esc(model.meta.legalBoundary)}</text></svg>`;
}
