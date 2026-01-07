/**
 * 基金业绩表格列配置
 * 定义所有可用的业绩指标列
 */

export interface ColumnConfig {
  key: string
  label: string
  category: string
  sortable: boolean
  defaultVisible: boolean
}

export const PERFORMANCE_COLUMNS: ColumnConfig[] = [
  // 基本信息列（总是显示）
  { key: 'fund_name', label: '产品名称', category: 'basic', sortable: false, defaultVisible: true },
  { key: 'manager_name', label: '管理人', category: 'basic', sortable: false, defaultVisible: true },
  { key: 'strategy_name', label: '策略', category: 'basic', sortable: false, defaultVisible: true },

  // 短期收益
  { key: 'weekly_return', label: '周收益', category: 'short_term', sortable: true, defaultVisible: false },
  { key: 'weekly_excess', label: '周超额', category: 'short_term', sortable: true, defaultVisible: false },
  { key: 'monthly_return', label: '月收益', category: 'short_term', sortable: true, defaultVisible: false },
  { key: 'monthly_excess', label: '月超额', category: 'short_term', sortable: true, defaultVisible: true },
  { key: 'monthly_max_drawdown', label: '月最大回撤', category: 'short_term', sortable: true, defaultVisible: false },

  // 中期收益
  { key: 'quarterly_return', label: '季收益', category: 'medium_term', sortable: true, defaultVisible: true },
  { key: 'quarterly_max_drawdown', label: '季最大回撤', category: 'medium_term', sortable: true, defaultVisible: false },
  { key: 'semi_annual_return', label: '半年收益(年化)', category: 'medium_term', sortable: true, defaultVisible: false },
  { key: 'semi_annual_excess', label: '半年超额(年化)', category: 'medium_term', sortable: true, defaultVisible: false },
  { key: 'semi_annual_max_drawdown', label: '半年最大回撤', category: 'medium_term', sortable: true, defaultVisible: false },

  // 年度收益
  { key: 'annual_return_ytd', label: '年收益(年化)', category: 'annual', sortable: true, defaultVisible: false },
  { key: 'annual_excess', label: '年超额(年化)', category: 'annual', sortable: true, defaultVisible: true },
  { key: 'annual_max_drawdown', label: '年最大回撤', category: 'annual', sortable: true, defaultVisible: false },
  { key: 'ytd_return', label: '今年以来收益', category: 'annual', sortable: true, defaultVisible: false },
  { key: 'ytd_excess', label: '今年以来超额', category: 'annual', sortable: true, defaultVisible: false },
  { key: 'ytd_max_drawdown', label: '今年以来回撤', category: 'annual', sortable: true, defaultVisible: false },

  // 成立以来
  { key: 'annual_return', label: '年化收益', category: 'inception', sortable: true, defaultVisible: true },
  { key: 'cumulative_return', label: '累计收益', category: 'inception', sortable: true, defaultVisible: true },
  { key: 'max_drawdown', label: '最大回撤', category: 'inception', sortable: true, defaultVisible: true },
  { key: 'annual_volatility', label: '年化波动率', category: 'inception', sortable: true, defaultVisible: false },

  // 风险调整指标
  { key: 'annual_sharpe', label: '夏普比率', category: 'risk_adjusted', sortable: true, defaultVisible: true },
  { key: 'annual_calmar', label: '卡玛比率', category: 'risk_adjusted', sortable: true, defaultVisible: false },
  { key: 'annual_sortino', label: '索提诺比率', category: 'risk_adjusted', sortable: true, defaultVisible: false },
  { key: 'inception_sharpe', label: '成立以来夏普', category: 'risk_adjusted', sortable: true, defaultVisible: false },
  { key: 'inception_calmar', label: '成立以来卡玛', category: 'risk_adjusted', sortable: true, defaultVisible: false },
  { key: 'inception_sortino', label: '成立以来索提诺', category: 'risk_adjusted', sortable: true, defaultVisible: false },
]

export const COLUMN_CATEGORIES = {
  basic: '基本信息',
  short_term: '短期收益',
  medium_term: '中期收益',
  annual: '年度收益',
  inception: '成立以来',
  risk_adjusted: '风险调整指标',
}

// 获取默认显示的列
export function getDefaultVisibleColumns(): string[] {
  return PERFORMANCE_COLUMNS.filter(col => col.defaultVisible).map(col => col.key)
}

// 按类别分组列
export function getColumnsByCategory() {
  const grouped: Record<string, ColumnConfig[]> = {}
  PERFORMANCE_COLUMNS.forEach(col => {
    if (!grouped[col.category]) {
      grouped[col.category] = []
    }
    grouped[col.category].push(col)
  })
  return grouped
}
