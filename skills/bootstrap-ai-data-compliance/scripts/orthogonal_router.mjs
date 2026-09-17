const ROUTE_HINTS = {
  DFE01: [['bottom', -48], [94.5, 470], [602.5, 470], ['bottom', 0]],
  DFE02: [['right', -18], ['left', -18]],
  DFE03: [['right', 0], ['left', 0]],
  DFE04: [['top', -45], [327.5, 270], [560, 270], ['bottom', -42.5]],
  DFE05: [['top', 42.5], ['bottom', 42.5]],
  DFE06: [['right', 18], ['left', 18]],
  DFE07: [['right', 0], ['left', 0]],
  DFE08: [['bottom', -32.5], ['top', -32.5]],
  DFE09: [['bottom', 0], ['top', 0]],
  DFE10: [['right', -12], ['left', -12]],
  DFE11: [['bottom', -42.5], ['top', -42.5]],
  DFE12: [['left', -18], ['right', -18]],
  DFE13: [['left', 18], ['right', 18]],
  DFE14: [['bottom', 0], [1062.5, 852], [28, 852], [28, 182], ['left', 0]],
  DFE15: [['bottom', 27.5], [1550, 900], [255, 900], [255, 250], [372.5, 250], ['bottom', 0]],
  DFE16: [['right', -18], ['left', -18]],
  DFE17: [['bottom', 0], [1522.5, 280], [1408, 280], [1408, 382], ['right', 0]],
  DFE18: [['left', -18], ['right', -18]],
  DFE19: [['bottom', -52.5], [1240, 872], [840, 872], [840, 824], ['bottom', 7.5]],
  DFE20: [['bottom', -72.5], [1220, 260], [1177, 260], [1177, 690], [832.5, 690], ['top', 0]],
  DFE21: [['left', 18], [700, 790], [700, 520], [372.5, 520], ['bottom', 0]],
  DFE22: [['left', 18], [28, 790], [28, 250], [142.5, 250], ['bottom', 0]]
};

const round = (value) => Math.round(value * 10) / 10;

function port(node, side, offset, nodeWidth, nodeHeight) {
  const centerX = node.x + nodeWidth / 2;
  const centerY = node.y + nodeHeight / 2;
  if (side === 'left') return { x: node.x, y: centerY + offset };
  if (side === 'right') return { x: node.x + nodeWidth, y: centerY + offset };
  if (side === 'top') return { x: centerX + offset, y: node.y };
  return { x: centerX + offset, y: node.y + nodeHeight };
}

function compress(points) {
  const unique = points.filter((point, index) => index === 0 || point.x !== points[index - 1].x || point.y !== points[index - 1].y);
  return unique.filter((point, index) => {
    if (index === 0 || index === unique.length - 1) return true;
    const previous = unique[index - 1];
    const next = unique[index + 1];
    return !((previous.x === point.x && point.x === next.x) || (previous.y === point.y && point.y === next.y));
  });
}

export function segmentIntersectsRect(a, b, rect, padding = 0) {
  const left = rect.x - padding;
  const right = rect.x + rect.width + padding;
  const top = rect.y - padding;
  const bottom = rect.y + rect.height + padding;
  if (a.x === b.x) return a.x > left && a.x < right && Math.max(a.y, b.y) > top && Math.min(a.y, b.y) < bottom;
  if (a.y === b.y) return a.y > top && a.y < bottom && Math.max(a.x, b.x) > left && Math.min(a.x, b.x) < right;
  return true;
}

function fallbackHint(from, to, index, nodeWidth, nodeHeight) {
  const fromCenter = { x: from.x + nodeWidth / 2, y: from.y + nodeHeight / 2 };
  const toCenter = { x: to.x + nodeWidth / 2, y: to.y + nodeHeight / 2 };
  const offset = ((index % 5) - 2) * 12;
  if (Math.abs(toCenter.x - fromCenter.x) >= Math.abs(toCenter.y - fromCenter.y)) {
    const startSide = toCenter.x >= fromCenter.x ? 'right' : 'left';
    const endSide = toCenter.x >= fromCenter.x ? 'left' : 'right';
    const start = port(from, startSide, offset, nodeWidth, nodeHeight);
    const end = port(to, endSide, -offset, nodeWidth, nodeHeight);
    const midX = round((start.x + end.x) / 2 + offset);
    return [start, { x: midX, y: start.y }, { x: midX, y: end.y }, end];
  }
  const startSide = toCenter.y >= fromCenter.y ? 'bottom' : 'top';
  const endSide = toCenter.y >= fromCenter.y ? 'top' : 'bottom';
  const start = port(from, startSide, offset, nodeWidth, nodeHeight);
  const end = port(to, endSide, -offset, nodeWidth, nodeHeight);
  const midY = round((start.y + end.y) / 2 + offset);
  return [start, { x: start.x, y: midY }, { x: end.x, y: midY }, end];
}

function labelPosition(points) {
  const segments = points.slice(1).map((point, index) => {
    const start = points[index];
    return {
      start,
      end: point,
      horizontal: start.y === point.y,
      length: Math.abs(point.x - start.x) + Math.abs(point.y - start.y)
    };
  });
  const horizontal = segments.filter((segment) => segment.horizontal && segment.length >= 54);
  const chosen = (horizontal.length ? horizontal : segments).sort((a, b) => b.length - a.length)[0];
  return {
    labelX: round((chosen.start.x + chosen.end.x) / 2),
    labelY: round((chosen.start.y + chosen.end.y) / 2 - (chosen.horizontal ? 11 : 0))
  };
}

export function routeOrthogonalEdge({ edge, index = 0, nodes, nodeWidth, nodeHeight }) {
  const nodeById = nodes instanceof Map ? nodes : new Map(nodes.map((node) => [node.id, node]));
  const from = nodeById.get(edge.from);
  const to = nodeById.get(edge.to);
  if (!from || !to) throw new Error(`Unknown data-flow endpoint: ${edge.id}`);

  const hint = ROUTE_HINTS[edge.id];
  const rawPoints = hint
    ? hint.map((item, itemIndex) => {
      if (typeof item[0] === 'string') return port(itemIndex === 0 ? from : to, item[0], item[1] ?? 0, nodeWidth, nodeHeight);
      return { x: item[0], y: item[1] };
    })
    : fallbackHint(from, to, index, nodeWidth, nodeHeight);
  const points = compress(rawPoints.map((point) => ({ x: round(point.x), y: round(point.y) })));
  for (let pointIndex = 1; pointIndex < points.length; pointIndex += 1) {
    const previous = points[pointIndex - 1];
    const current = points[pointIndex];
    if (previous.x !== current.x && previous.y !== current.y) throw new Error(`${edge.id} contains a diagonal route segment`);
  }
  const { labelX, labelY } = labelPosition(points);
  return {
    points,
    d: points.map((point, pointIndex) => `${pointIndex ? 'L' : 'M'} ${point.x} ${point.y}`).join(' '),
    labelX,
    labelY
  };
}
