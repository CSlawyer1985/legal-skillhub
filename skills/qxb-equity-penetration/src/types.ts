/**
 * API 响应基础类型
 */
export interface ApiResponse<T = any> {
  status: string
  message: string
  data: T
}

/**
 * 路径节点
 */
export interface PathNode {
  name: string
  percent: string
}

/**
 * 直接股东项
 */
export interface ShareholderItem {
  name: string
  stockPercent: string
}

/**
 * 间接股东项
 */
export interface IndirectShareholderItem {
  name: string
  stockPercent: string
  shortestLevel: number
  shortestPath: PathNode[]
}

/**
 * 直接股东
 */
export interface DirectShareholders {
  total: number
  items: ShareholderItem[]
}

/**
 * 间接股东
 */
export interface IndirectShareholders {
  total: number
  items: IndirectShareholderItem[]
}

/**
 * 股权穿透结果
 */
export interface EquityPenetration {
  ename: string
  directShareholders: DirectShareholders
  indirectShareholders: IndirectShareholders
}
