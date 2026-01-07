import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { StrategyPieChart } from '@/components/charts/StrategyPieChart'
import { ColumnSelector } from '@/components/ColumnSelector'
import { getStats, getStrategies, getFunds, getStrategyDistribution, getReportDates, type Strategy, type Fund } from '@/lib/api'
import { formatPercent, formatDate, formatNumber } from '@/lib/utils'
import { PERFORMANCE_COLUMNS, getDefaultVisibleColumns } from '@/lib/columnConfig'
import { Building2, Briefcase, TrendingUp, Calendar, ChevronLeft, ChevronRight } from 'lucide-react'

const STORAGE_KEY = 'dashboard_visible_columns'

export function Dashboard() {
  const [selectedStrategy, setSelectedStrategy] = useState<number | undefined>()
  const [selectedReportDate, setSelectedReportDate] = useState<string | undefined>()
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('annual_return')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [visibleColumns, setVisibleColumns] = useState<string[]>(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : getDefaultVisibleColumns()
  })
  const pageSize = 20

  // 保存列选择到localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(visibleColumns))
  }, [visibleColumns])

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', selectedReportDate],
    queryFn: () => getStats(selectedReportDate),
    enabled: !!selectedReportDate,
  })

  const { data: strategies } = useQuery({
    queryKey: ['strategies', selectedReportDate],
    queryFn: () => getStrategies(selectedReportDate),
    enabled: !!selectedReportDate,
  })

  const { data: reportDates } = useQuery({
    queryKey: ['report-dates'],
    queryFn: getReportDates,
  })

  // 当报告日期列表加载后，自动选择最新日期
  useEffect(() => {
    if (reportDates?.dates && reportDates.dates.length > 0 && !selectedReportDate) {
      setSelectedReportDate(reportDates.dates[0])
    }
  }, [reportDates, selectedReportDate])

  const { data: distribution } = useQuery({
    queryKey: ['distribution', selectedReportDate],
    queryFn: () => getStrategyDistribution(selectedReportDate),
    enabled: !!selectedReportDate,
  })

  const { data: fundsData, isLoading: fundsLoading } = useQuery({
    queryKey: ['funds-ranking', selectedStrategy, selectedReportDate, page, sortBy, sortOrder],
    queryFn: () => getFunds({
      strategy_id: selectedStrategy,
      report_date: selectedReportDate,
      sort_by: sortBy,
      order: sortOrder,
      page,
      page_size: pageSize,
    }),
    enabled: !!selectedReportDate,
  })

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
    setPage(1)
  }

  const handleStrategyChange = (strategyId: number | undefined) => {
    setSelectedStrategy(strategyId)
    setPage(1)
  }

  const SortHeader = ({ field, children }: { field: string; children: React.ReactNode }) => {
    const column = PERFORMANCE_COLUMNS.find(col => col.key === field)
    const align = column?.category === 'basic' ? 'left' : 'right'

    return (
      <TableHead
        className={`${align === 'right' ? 'text-right' : ''} ${column?.sortable ? 'cursor-pointer hover:bg-muted/50 select-none' : ''}`}
        onClick={() => column?.sortable && handleSort(field)}
      >
        <div className={`flex items-center ${align === 'right' ? 'justify-end' : 'justify-start'} gap-1`}>
          {children}
          {column?.sortable && sortBy === field && (
            <span className="text-xs">{sortOrder === 'desc' ? '↓' : '↑'}</span>
          )}
        </div>
      </TableHead>
    )
  }

  // 获取单元格内容
  const getCellContent = (fund: Fund, columnKey: string) => {
    switch (columnKey) {
      case 'fund_name':
        return (
          <TableCell className="max-w-[180px] truncate" title={fund.fund_name}>
            {fund.fund_name}
          </TableCell>
        )
      case 'manager_name':
        return (
          <TableCell className="max-w-[120px] truncate" title={fund.manager_name || ''}>
            {fund.manager_name || '-'}
          </TableCell>
        )
      case 'strategy_name':
        return (
          <TableCell className="max-w-[120px] truncate" title={fund.strategy_name || ''}>
            {fund.strategy_name || '-'}
          </TableCell>
        )
      default:
        // 业绩数据字段
        const value = fund.latest_performance?.[columnKey as keyof typeof fund.latest_performance]
        const numValue = typeof value === 'number' ? value : null

        // 判断是否为比率字段（夏普、卡玛、索提诺）
        const isRatio = columnKey.includes('sharpe') || columnKey.includes('calmar') || columnKey.includes('sortino')

        // 收益类指标用红绿色，回撤和波动率用红色，比率不着色
        let colorClass = ''
        if (!isRatio && numValue !== null) {
          if (columnKey.includes('drawdown') || columnKey.includes('volatility')) {
            colorClass = 'text-red-600'
          } else {
            colorClass = numValue >= 0 ? 'text-green-600' : 'text-red-600'
          }
        }

        return (
          <TableCell className={`text-right ${colorClass}`}>
            {isRatio ? formatNumber(numValue) : formatPercent(numValue)}
          </TableCell>
        )
    }
  }

  // 获取可见列配置
  const visibleColumnConfigs = PERFORMANCE_COLUMNS.filter(col =>
    visibleColumns.includes(col.key)
  )

  if (statsLoading) {
    return <div className="flex items-center justify-center h-64">加载中...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">数据总览</h1>
        {/* Report Date Selector */}
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">周报日期:</span>
          <select
            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm font-medium"
            value={selectedReportDate || ''}
            onChange={(e) => {
              setSelectedReportDate(e.target.value)
              setPage(1)
            }}
          >
            {reportDates?.dates?.map((date: string) => (
              <option key={date} value={date}>
                {date.replace(/-/g, '')}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">管理人</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_managers?.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">私募基金管理人</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">策略分类</CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_strategies}</div>
            <p className="text-xs text-muted-foreground">投资策略类型</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">产品数量</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_funds?.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">私募基金产品</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">最新报告</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatDate(stats?.latest_report_date)}</div>
            <p className="text-xs text-muted-foreground">最近一期周报</p>
          </CardContent>
        </Card>
      </div>

      {/* Strategy Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>策略分布</CardTitle>
        </CardHeader>
        <CardContent>
          {distribution?.items && (
            <StrategyPieChart data={distribution.items} title="" />
          )}
        </CardContent>
      </Card>

      {/* Fund Rankings Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-4">
            <CardTitle>
              基金业绩排名
              {fundsData && (
                <span className="text-sm font-normal text-muted-foreground ml-2">
                  共 {fundsData.total} 只基金
                </span>
              )}
            </CardTitle>
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">策略筛选:</span>
              <select
                className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                value={selectedStrategy || ''}
                onChange={(e) => handleStrategyChange(e.target.value ? Number(e.target.value) : undefined)}
              >
                <option value="">全部策略</option>
                {strategies?.items?.map((s: Strategy) => (
                  <option key={s.strategy_id} value={s.strategy_id}>
                    {s.strategy_name.length > 25 ? s.strategy_name.substring(0, 25) + '...' : s.strategy_name}
                    ({s.fund_count})
                  </option>
                ))}
              </select>
              <ColumnSelector
                visibleColumns={visibleColumns}
                onColumnsChange={setVisibleColumns}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {fundsLoading ? (
            <div className="flex items-center justify-center h-32">加载中...</div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">排名</TableHead>
                      {visibleColumnConfigs.map(column => (
                        <SortHeader key={column.key} field={column.key}>
                          {column.label}
                        </SortHeader>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fundsData?.items?.map((fund: Fund, index: number) => (
                      <TableRow key={fund.fund_code}>
                        <TableCell className="font-medium">
                          {(page - 1) * pageSize + index + 1}
                        </TableCell>
                        {visibleColumnConfigs.map(column => (
                          <React.Fragment key={column.key}>
                            {getCellContent(fund, column.key)}
                          </React.Fragment>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {fundsData && fundsData.total_pages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-muted-foreground">
                    第 {page} / {fundsData.total_pages} 页
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      上一页
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.min(fundsData.total_pages, p + 1))}
                      disabled={page === fundsData.total_pages}
                    >
                      下一页
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
