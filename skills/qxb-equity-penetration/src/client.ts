import axios, { AxiosInstance } from 'axios'
import { ApiResponse, EquityPenetration } from './types'

const DEFAULT_API_TOKEN = process.env.QXBENT_API_TOKEN

/**
 * 启信宝企业股权穿透查询客户端
 */
export class QxbEquityPenetrationClient {
  private client: AxiosInstance

  constructor(apiToken: string, baseURL: string = 'https://external-api.qixin.com/skill/ent/public') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
        'x-api-token': apiToken,
      },
      timeout: 30000,
    })
  }

  /**
   * 查询企业股权穿透
   * @param ename 企业名称
   * @returns 股权穿透结果
   */
  async getEquityPenetration(ename: string): Promise<EquityPenetration> {
    const response = await this.client.post<ApiResponse<EquityPenetration>>(
      '/enterprise/getEquityPenetration',
      { ename }
    )

    if (response.data.status !== '1') {
      throw new Error(response.data.message || '查询失败')
    }

    return response.data.data
  }

  /**
   * 通过企业ID查询股权穿透
   * @param eid 企业ID
   * @returns 股权穿透结果
   */
  async getEquityPenetrationByEid(eid: string): Promise<EquityPenetration> {
    const response = await this.client.post<ApiResponse<EquityPenetration>>(
      '/enterprise/getEquityPenetration',
      { eid }
    )

    if (response.data.status !== '1') {
      throw new Error(response.data.message || '查询失败')
    }

    return response.data.data
  }
}

/**
 * 创建客户端实例
 * @param apiToken API Token，可选，默认从环境变量 QXBENT_API_TOKEN 读取
 */
export function createClient(apiToken?: string): QxbEquityPenetrationClient {
  const token = apiToken || DEFAULT_API_TOKEN
  if (!token) {
    throw new Error('请提供 API Token 或设置环境变量 QXBENT_API_TOKEN')
  }
  return new QxbEquityPenetrationClient(token)
}
