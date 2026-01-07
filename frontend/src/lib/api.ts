/**
 * API 调用模块
 *
 * 封装所有与后端 API 的交互，包括：
 * - Axios 实例配置
 * - TypeScript 类型定义
 * - API 调用函数
 *
 * 后端 API 地址：http://localhost:8000/api
 */

import axios from 'axios'

/** API 基础地址，生产环境需要修改 */
const API_BASE_URL = 'http://localhost:8000/api'

/** Axios 实例，统一配置请求头和基础URL */
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ==================== 类型定义 ====================

/** 统计概览数据 */
export interface Stats {
  total_managers: number      // 管理人总数
  total_strategies: number    // 策略总数
  total_funds: number         // 基金产品总数
  total_performances: number  // 业绩记录总数
  latest_report_date: string | null  // 最新报告日期
}

/** 管理人信息 */
export interface Manager {
  manager_id: number
  manager_name: string
  establishment_date: string | null  // 成立日期
  company_size: string | null        // 公司规模
  fund_count: number                 // 旗下基金数量
}

/** 策略分类信息 */
export interface Strategy {
  strategy_id: number
  strategy_name: string              // 策略名称（level3_category）
  level1_category: string | null     // 一级分类
  level2_category: string | null     // 二级分类
  fund_count: number                 // 该策略基金数量
}

/** 基金产品信息 */
export interface Fund {
  fund_code: string                  // 产品代码
  fund_name: string                  // 产品名称
  manager_id: number | null
  manager_name: string | null        // ��理人名称
  strategy_id: number | null
  strategy_name: string | null       // 策略名称
  launch_date: string | null         // 成立日期
  latest_performance?: PerformanceSnapshot  // 最新业绩快照
}

/**
 * 业绩快照
 * 注意：所有收益率/回撤字段均为小数形式，如 0.1234 表示 12.34%
 */
export interface PerformanceSnapshot {
  report_date: string
  weekly_return: number | null       // 周收益
  monthly_return: number | null      // 月收益
  quarterly_return: number | null    // 季收益
  annual_return: number | null       // 年化收益（成立以来）
  cumulative_return: number | null   // 累计收益
  max_drawdown: number | null        // 最大回撤
  annual_sharpe: number | null       // 夏普比率
  annual_volatility: number | null   // 年化波动率
}

/** 排名项 */
export interface RankingItem {
  rank: number
  fund_code: string
  fund_name: string
  manager_name: string | null
  strategy_name: string | null
  value: number | null               // 排名指标值
  report_date: string
}

/** 策略分布（用于饼图） */
export interface StrategyDistribution {
  name: string   // 策略名称
  value: number  // 基金数量
}

// ==================== API 函数 ====================

/**
 * 获取统计概览
 * @param reportDate 可选，指定报告日期
 */
export async function getStats(reportDate?: string): Promise<Stats> {
  const { data } = await api.get('/analytics/stats', {
    params: { report_date: reportDate }
  })
  return data
}

/**
 * 获取管理人列表
 * @param keyword 搜索关键词
 * @param page 页码
 * @param pageSize 每页数量
 */
export async function getManagers(keyword?: string, page = 1, pageSize = 20) {
  const { data } = await api.get('/managers', {
    params: { keyword, page, page_size: pageSize }
  })
  return data
}

/**
 * 获取策略列表
 * @param reportDate 可选，用于统计该日期的基金数量
 */
export async function getStrategies(reportDate?: string) {
  const { data } = await api.get('/strategies', {
    params: { report_date: reportDate }
  })
  return data
}

/**
 * 搜索基金产品
 * @param params 搜索参数
 * @param params.keyword 搜索关键词（产品名称/管理人/代码）
 * @param params.strategy_id 策略ID筛选
 * @param params.sort_by 排序字段
 * @param params.order 排序方向 asc/desc
 * @param params.page 页码
 * @param params.page_size 每页数量
 * @param params.report_date 报告日期
 */
export async function getFunds(params: {
  keyword?: string
  manager_id?: number
  strategy_id?: number
  min_annual_return?: number
  max_drawdown?: number
  min_sharpe?: number
  sort_by?: string
  order?: string
  page?: number
  page_size?: number
  report_date?: string
}) {
  const { data } = await api.get('/funds', { params })
  return data
}

/**
 * 获取基金详情
 * @param fundCode 基金代码
 */
export async function getFundDetail(fundCode: string) {
  const { data } = await api.get(`/funds/${fundCode}`)
  return data
}

/**
 * 获取基金历史业绩
 * @param fundCode 基金代码
 * @param startDate 开始日期
 * @param endDate 结束日期
 */
export async function getFundPerformance(fundCode: string, startDate?: string, endDate?: string) {
  const { data } = await api.get(`/funds/${fundCode}/performance`, {
    params: { start_date: startDate, end_date: endDate }
  })
  return data
}

/**
 * 获取业绩排名
 * @param params.metric 排名指标，如 annual_return, annual_sharpe
 * @param params.report_date 报告日期
 * @param params.strategy_id 策略筛选
 * @param params.limit 返回数量
 */
export async function getRanking(params: {
  metric?: string
  report_date?: string
  strategy_id?: number
  limit?: number
}) {
  const { data } = await api.get('/analytics/ranking', { params })
  return data
}

/**
 * 获取策略分布数据（用于饼图）
 * @param reportDate 报告日期
 */
export async function getStrategyDistribution(reportDate?: string) {
  const { data } = await api.get('/analytics/strategy-distribution', {
    params: { report_date: reportDate }
  })
  return data
}

/** 获取所有报告元数据 */
export async function getReports() {
  const { data } = await api.get('/analytics/reports')
  return data
}

/** 获取可用的报告日期列表 */
export async function getReportDates(): Promise<{ dates: string[] }> {
  const { data } = await api.get('/analytics/report-dates')
  return data
}

/**
 * 多产品对比
 * @param fundCodes 要对比的基金代码数组（2-5个）
 * @param startDate 开始日期
 * @param endDate 结束日期
 */
export async function compareFunds(fundCodes: string[], startDate?: string, endDate?: string) {
  const { data } = await api.post('/analytics/compare', {
    fund_codes: fundCodes,
    start_date: startDate,
    end_date: endDate
  })
  return data
}
